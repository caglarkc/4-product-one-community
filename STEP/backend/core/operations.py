import os
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .common import *
from .accounts import POLICY_KEYS,initial_grants
from .serialization import dto
from .market import refund_job
from .contracts import investigation,week_totals
from .payments import run_operation,release_target,entries,operation_dto

@transaction.atomic
def messaging(request,id=None,action=None):
    if not id:
        rows=Conversation.objects.filter(Q(users=request.user)|Q(contract__workers__user=request.user)).distinct().order_by('-created_at');return page(request,rows,dto)
    row=object_get(Conversation,id);conversation_access(request.user,row)
    if action!='messages':return dto(row)
    if request.method=='GET':return page(request,row.messages.select_related('sender').order_by('created_at'),dto)
    data=request.data;require(data.get('text') or data.get('attachment_ids'),'message_empty','Mesaj veya dosya gerekir.',400)
    assets=[]
    for id in data.get('attachment_ids',[]):
        a=object_get(Asset,id);require(a.owner_id==request.user.pk and a.captured_at is None and (a.conversation_id==row.pk or (row.contract_id and a.contract_id==row.contract_id)),'file_scope','Mesaj dosyası başka kapsamdan alınamaz.',400);assets.append(a)
    m=Message.objects.create(conversation=row,sender=request.user,text=data.get('text',''));m.attachments.set(assets)
    for user in row.users.exclude(pk=request.user.pk):notify(user,'message.received','STEP görüşmesinde yeni mesaj var.',m)
    return dto(m)

@transaction.atomic
def attachments(request):
    from .tracking import save_asset
    data=request.data;targets=[x for x in ['contract','conversation','job'] if data.get(x)];require(len(targets)==1,'attachment_scope','Tek dosya kapsamı gerekir.',400);scope=targets[0]
    contract=object_get(Contract,data['contract']) if scope=='contract' else None;conversation=object_get(Conversation,data['conversation']) if scope=='conversation' else None;job=object_get(Job,data['job']) if scope=='job' else None
    if contract:contract_access(request.user,contract)
    if conversation:conversation_access(request.user,conversation)
    if job:require(job.owner_id==request.user.pk)
    return dto(save_asset(request.user,request.FILES.get('file'),contract=contract,conversation=conversation,job=job))

@transaction.atomic
def ratings(request,id):
    c=object_get(Contract,id,True);contract_access(request.user,c,True)
    if request.method=='GET':return page(request,c.ratings.order_by('-created_at'),dto)
    score=int(request.data.get('score',0));require(1<=score<=5,'score_invalid','Puan 1–5 olmalıdır.',400)
    party='employer' if request.user.pk==c.employer_id else 'freelancer';require(not c.ratings.filter(party=party).exists(),'already_rated','Taraf değerlendirmesi zaten var.',409)
    return dto(Rating.objects.create(contract=c,author=request.user,party=party,score=score,comment=request.data.get('comment','')))

@transaction.atomic
def claim(request):
    require(request.user.is_staff);fields(request.data,['case_type','case_id','reason']);kind=request.data['case_type'];require(kind in ['privacy','dispute'],'case_type','İnceleme türü gerekir.',400)
    case=object_get(PrivacyRequest if kind=='privacy' else Dispute,request.data['case_id'],True)
    require(case.status==('pending' if kind=='privacy' else 'open'),'case_closed','İnceleme dosyası kapalı.',409);contract=case.asset.contract if kind=='privacy' else case.contract
    require(request.user.is_superuser or request.user.has_perm('core.change_'+('privacyrequest' if kind=='privacy' else 'dispute')),'operator_permission','Bu inceleme türü için görev yetkisi gerekir.')
    grant=InvestigationGrant.objects.create(operator=request.user,contract=contract,case_type=kind,case_id=case.pk,reason=request.data['reason'],expires_at=timezone.now()+timedelta(hours=8));audit(request.user,grant,request.data['reason'],'investigation.claim');return {'id':grant.pk,'contract':contract.pk,'case_id':case.pk,'case_type':kind,'expires_at':grant.expires_at}

@transaction.atomic
def admin_endpoint(request,action,id=None):
    require(request.user.is_staff,'operator_required','Yönetim yetkisi gerekir.')
    u=request.user;data=request.data
    if action=='overview':return {'users':User.objects.count(),'jobs':Job.objects.count(),'contracts':Contract.objects.count(),'open_cases':Report.objects.filter(status='pending').count()+Dispute.objects.filter(status='open').count()+PrivacyRequest.objects.filter(status='pending').count()}
    if action=='policy':
        p=Policy.objects.select_for_update().get_or_create(pk=1)[0]
        if request.method=='PATCH':
            require(u.is_superuser or u.has_perm('core.change_policy'));require(set(data)<=POLICY_KEYS,'policy_fields','Geçersiz politika alanı.',400)
            for key,value in data.items():
                if value is None:continue
                if key=='capabilities':require(isinstance(value,dict) and all(isinstance(v,bool) or (k=='withdrawal_strategy' and v in ['marketplace_settlement_reconciliation','unavailable']) for k,v in value.items()),'capability_format','Kabiliyetler boolean gerekir.',400)
                elif key=='withdraw_schedule':require(isinstance(value,str) and value.strip(),'schedule_invalid','Operasyon çekim takvimi gerekir.',400)
                elif key in ['credit_price','withdraw_minimum']:money(value)
                else:require(isinstance(value,int) and value>=0 and (key not in ['boost_hours','idle_seconds'] or value>0),'policy_value','Geçerli sayısal politika gerekir.',400)
            p.values={**p.values,**dict(data)};p.save();audit(u,p,'Yönetim politika yapılandırması','policy.update')
        return p.values
    if action in ['universities','categories']:
        model=University if action=='universities' else Category
        if request.method=='GET':return page(request,model.objects.order_by('name'),dto)
        require(request.method=='POST' or (request.method=='PATCH' and id is not None),'method_not_allowed','Koleksiyonda GET/POST; kayıt üzerinde PATCH gerekir.',405)
        require(u.is_superuser or u.has_perm('core.'+('change_' if id else 'add_')+model.__name__.lower()),'operator_permission','Yapılandırma değiştirme yetkisi gerekir.')
        fields(data,['name']);kwargs={'name':str(data['name'])}
        if model is University:
            domains=data.get('domains',[]);require(isinstance(domains,list) and domains and all(isinstance(d,str) and '.' in d and '@' not in d and '/' not in d and d==d.casefold() for d in domains),'domains_invalid','Normalize üniversite alan adları gerekir.',400);kwargs['domains']=domains
        if id:
            row=object_get(model,id,True)
            for key,value in kwargs.items():setattr(row,key,value)
            row.save()
        else:row=model.objects.create(**kwargs)
        audit(u,row,'Yönetim yapılandırması','update' if id else 'create');return dto(row)
    if action=='credit-grants':
        require(u.is_superuser or u.has_perm('core.add_creditentry'),'operator_permission','Test kredi yetkisi gerekir.')
        require(settings.STEP_MODE=='test','test_grant_only','Test kredileri canlıda verilmez.',409);fields(data,['credits','reason']);require(isinstance(data['credits'],int) and data['credits']>0,'credits_invalid','Pozitif tam kredi gerekir.',400);require(bool(data.get('user'))!=bool(data.get('team')),'wallet_target','Tek bakiye hedefi gerekir.',400)
        if data.get('team'):
            t=object_get(Team,data['team']);wallet=wallet_for(t.leader,t)
        else:wallet=wallet_for(object_get(User,data['user']))
        entry=credit_change(wallet,data['credits'],'test_grant','grant:'+str(__import__('uuid').uuid4()));audit(u,entry,data['reason'],'credit.grant');return dto(wallet)
    if action=='queue':return {'reports':[dto(x) for x in Report.objects.filter(status='pending')],'disputes':[dto(x) for x in Dispute.objects.filter(status='open')],'privacy_requests':[dto(x) for x in PrivacyRequest.objects.filter(status='pending')],'verification_requests':[dto(x) for x in EmployerVerification.objects.filter(status='pending')],'credit_refunds':[dto(x) for x in RefundRequest.objects.filter(status='pending')],'leader_changes':[dto(x) for x in LeaderChange.objects.filter(status='pending')],'payouts':[dto(x) for x in Payout.objects.filter(status__in=['requested','processing','unavailable'])],'payments':[dto(x) for x in Payment.objects.filter(status__in=['pending','failed','unknown'])],'provider_operations':[operation_dto(o) for o in ProviderOperation.objects.filter(state__in=['pending','blocked','processing','unknown','failed'])],'pending_manual_time':[dto(x) for x in ManualTime.objects.filter(status='pending',ends_at__lt=timezone.now())],'pending_offline_grants':[dto(x) for x in WorkSession.objects.filter(stopped_at=None,ends_at__lt=timezone.now())]}
    if action=='audit':return page(request,AuditEvent.objects.order_by('-created_at'),dto)
    if action=='reports':
        require(u.is_superuser or u.has_perm('core.change_report'),'operator_permission','İlan moderasyon yetkisi gerekir.')
        row=object_get(Report,id,True);fields(data,['decision','reason']);require(row.status=='pending' and data['decision'] in ['keep','remove'],'case_state','Geçerli şikâyet kararı gerekir.',409)
        if data['decision']=='remove':job=object_get(Job,row.job_id,True);job.status='removed';job.save();refund_job(job)
        row.status='resolved';row.save();audit(u,row,data['reason'],data['decision']);return dto(row)
    if action=='verifications':
        require(u.is_superuser or u.has_perm('core.change_employerverification'),'operator_permission','İşveren doğrulama yetkisi gerekir.')
        row=object_get(EmployerVerification,id,True);fields(data,['decision','reason']);require(data['decision'] in ['approve','reject'],'decision_invalid','Geçerli karar gerekir.',400)
        if data['decision']=='approve':
            fields(data,['identity_reference']);require(bool(row.phone_verified_at and row.verified_phone==row.details.get('phone')),'phone_unverified','Aynı telefonun OTP kanıtı gerekir.',409)
            if row.kind=='company':fields(data,['company_reference','authorized_reference'])
            for k in ['identity_reference','company_reference','authorized_reference']:setattr(row,k,str(data.get(k,''))[:300])
            row.status='verified'
        else:row.status='rejected'
        row.save();audit(u,row,data['reason'],data['decision']);return dto(row)
    raise Problem('not_found','Yönetim yolu bulunamadı.',404)


def process_payout(request,id):
    require(request.user.is_staff and (request.user.is_superuser or request.user.has_perm('core.change_payout')),'operator_permission','Çekim karar yetkisi gerekir.');fields(request.data,['reason']);row=object_get(Payout,id)
    require(row.status in ['requested','processing','unavailable'],'payout_state','Çekim sonuçlandı.',409)
    operation=ProviderOperation.objects.get(event_key='withdrawal:'+str(row.pk))
    outcome=request.data.get('outcome')
    fixture=row.mode=='simulator' and settings.DEBUG and settings.STEP_MODE=='test'
    if fixture:
        require(outcome in ['success','failure'],'fixture_outcome','Yerel fixture başarı/başarısızlık sonucu açıkça seçilmelidir.',400)
        proofs=[];success=outcome=='success'
    elif request.data.get('decision')=='reject':
        require(operation.state in ['blocked','failed'],'operation_pending','Belirsiz gönderilmiş banka işlemi kanıtsız iptal edilemez.',409);success=False;proofs=[]
    else:
        from .providers import PayoutGateway
        from .payments import capability
        capability('bank_reconciliation');gateway=PayoutGateway();result=gateway.request(row)
        if result['state']=='unavailable':
            with transaction.atomic():
                current=object_get(Payout,id,True);current.status='unavailable';current.failure_reason=result['code'];current.save();ProviderOperation.objects.filter(pk=operation.pk).update(state='blocked',result=result);audit(request.user,current,request.data['reason'],'withdrawal.capability_missing')
            return dto(current)
        proofs=gateway.reconcile(row)
        success=bool(proofs) and sum((Decimal(p['amount']) for p in proofs),Decimal('0'))==row.amount and all(p['bank_digest']==row.bank_digest for p in proofs)
        if not success:
            Payout.objects.filter(pk=row.pk).update(status='processing',failure_reason='awaiting_bound_bank_transfer_proof');ProviderOperation.objects.filter(pk=operation.pk).update(state='processing',result={'missing_operation':'transaction-bound on-demand bank proof','source_payments':result['sources']});return dto(Payout.objects.get(pk=row.pk))
    with transaction.atomic():
        row=object_get(Payout,id,True);require(row.status in ['requested','processing','unavailable'],'payout_finalized','Çekim zaten sonuçlandı; aynı rezerv yeniden kullanılamaz.',409);a=MoneyAccount.objects.select_for_update().get(user=row.owner,mode=row.mode);require(a.reserved>=row.amount,'reserve_missing','Çekim rezervi bulunamadı.',409);a.reserved-=row.amount
        if not success:a.available+=row.amount;row.status='failed';row.failure_reason='fixture_failure' if fixture else 'undispatched_operator_rejection'
        else:
            for proof in proofs:
                payment=object_get(Payment,proof['payment'],True);require(not BankSettlement.objects.filter(payment=payment).exists(),'bank_duplicate','Bu sağlayıcı kazancı daha önce banka aktarımı olarak kaydedildi.',409);BankSettlement.objects.create(payment=payment,payout=row,reference=proof['reference'],amount=Decimal(proof['amount']),bank_digest=row.bank_digest);payment.settlement_status='confirmed';payment.save()
            row.status='paid';row.provider_reference='fixture:'+str(row.pk) if fixture else ';'.join(p['reference'] for p in proofs);row.paid_at=timezone.now();entries(row.owner,'fixture_payout' if fixture else 'bank_payout',-row.amount,'payout-debit:'+str(row.pk),row.pk,row.mode);entries(None,'fixture_clearing' if fixture else 'bank_clearing',row.amount,'payout-credit:'+str(row.pk),row.pk,row.mode)
        a.save();row.save();operation.state='confirmed' if success else 'failed';operation.result={'fixture':fixture,'success':success,'bank_transfer_proven':success and not fixture};operation.save();audit(request.user,row,request.data['reason'],'fixture.payout' if fixture else ('bank.confirmed' if success else 'payout.failed'));return dto(row)

@transaction.atomic
def refund_requests(request,id=None):
    if id:
        require(request.user.is_staff and (request.user.is_superuser or request.user.has_perm('core.change_refundrequest')),'operator_permission','Kredi iade karar yetkisi gerekir.');row=object_get(RefundRequest,id,True);fields(request.data,['decision','reason']);require(row.status=='pending','refund_state','Talep kapalı.',409)
        choice=request.data['decision'];require(choice in ['approve','reject'],'decision_invalid','Geçerli karar gerekir.',400)
        if choice=='approve':
            from .payments import capability
            capability('credit_refund')
            p=row.purchase;w=Wallet.objects.select_for_update().get(pk=p.wallet_id)
            spent=CreditEntry.objects.filter(wallet=w,amount__lt=0,created_at__gte=p.created_at).exists();require(not spent and w.balance>=p.credits,'credits_used','Kullanılmamış kredi kanıtı gerekir.',409)
            payment=Payment.objects.select_for_update().filter(target_type='credit_purchase',target_id=p.pk,status='funded').first();require(payment is not None,'payment_missing','Satın alma ödemesi bulunamadı.',409)
            credit_change(w,-p.credits,'purchase_refund','purchase-refund:'+str(p.pk),p.pk);operation,_=ProviderOperation.objects.get_or_create(event_key='purchase-refund:'+str(p.pk),defaults={'payment':payment,'kind':'refund','payload':{'amount':str(payment.amount),'target_type':'credit_purchase','target_id':str(p.pk)}})
            p.status='refund_pending';p.save()
            if payment.mode=='simulator':
                from .payments import finish_operation
                finish_operation(operation,{})
        row.status='approved' if choice=='approve' else 'rejected';row.save();audit(request.user,row,request.data['reason'],choice);return dto(row)
    if request.method=='GET':return page(request,RefundRequest.objects.filter(owner=request.user).order_by('-created_at'),dto)
    fields(request.data,['purchase','reason']);p=object_get(CreditPurchase,request.data['purchase'],True);require(p.owner_id==request.user.pk and p.status=='funded');require(not RefundRequest.objects.filter(purchase=p,status__in=['pending','approved']).exists(),'refund_exists','İade talebi zaten var.',409);return dto(RefundRequest.objects.create(owner=request.user,purchase=p,reason=request.data['reason']))


def tick():
    environment_gate();now=timezone.now()
    Outbox.objects.filter(state='sending',lease_until__lt=now).update(state='retry')
    # Each row runs in a short transaction; financial services retain their own locks/predicates.
    for user_id in User.objects.filter(is_active=True).values_list('pk',flat=True).iterator():
        with transaction.atomic():
            u=User.objects.select_for_update(no_key=True).get(pk=user_id);initial_grants(u);initial_grants(u,True)
    Eligibility.objects.filter(status='verified',verified_until__lte=now).update(status='expired')
    for m in Milestone.objects.filter(status='submitted',review_due_at__lte=now).iterator():
        with transaction.atomic():
            row=object_get(Milestone,m.pk,True)
            if row.status=='submitted' and row.review_due_at and row.review_due_at<=timezone.now() and not Dispute.objects.filter(target_id=row.pk,status='open').exists():release_target(row)
    for w in Week.objects.filter(status__in=['funded','review']).iterator():
        with transaction.atomic():
            row=object_get(Week,w.pk,True)
            if row.status=='funded' and row.ends_at<=timezone.now() and not WorkSession.objects.filter(contract=row.contract,created_at__gte=row.starts_at,created_at__lt=row.ends_at,stopped_at=None).exists() and not ManualTime.objects.filter(contract=row.contract,status='pending',starts_at__gte=row.starts_at,ends_at__lte=row.ends_at).exists():week_totals(row);row.status='review';row.review_due_at=timezone.now()+timedelta(days=5);row.save()
            if row.status=='review' and row.review_due_at<=timezone.now() and not Dispute.objects.filter(target_id=row.pk,status='open').exists():release_target(row)
    for a in Asset.objects.filter(state='preview',publication_ready_at__isnull=False,publish_at__lte=now).iterator():
        with transaction.atomic():
            row=object_get(Asset,a.pk,True)
            if row.state=='preview' and row.publication_ready_at and row.publish_at and row.publish_at<=timezone.now() and not PrivacyRequest.objects.filter(asset=row,status='pending').exists():row.state='released';row.publish_at=None;row.save()
    for promotion in Promotion.objects.filter(ends_at__lte=now,refunded=False).iterator():
        model=Job if promotion.target_type=='job' else Application
        model.objects.filter(pk=promotion.target_id,boosted_until__lte=now).update(boosted_until=None)
    held=set(Dispute.objects.filter(status='open').values_list('contract_id',flat=True))
    for a in Asset.objects.filter(captured_at__lte=now-timedelta(days=90),purged_at=None).exclude(contract_id__in=held).iterator():
        with transaction.atomic():
            row=object_get(Asset,a.pk,True)
            if not Dispute.objects.filter(contract_id=row.contract_id,status='open').exists():
                (settings.PRIVATE_ROOT/row.storage_key).unlink(missing_ok=True);row.purged_at=now;row.save();TimeBlock.objects.filter(screenshot=row).update(active_app='',key_count=0,mouse_count=0)
    TimeBlock.objects.filter(ends_at__lte=now-timedelta(days=90)).exclude(session__contract_id__in=held).update(active_app='',key_count=0,mouse_count=0)
    # Crash/timeout after dispatch is unknown, never automatically repeated.
    ProviderOperation.objects.filter(state='processing',lease_until__lt=now).update(state='unknown')
    for id in ProviderOperation.objects.filter(state='pending').values_list('pk',flat=True):run_operation(id)
    for id in Outbox.objects.filter(state__in=['pending','retry'],next_at__lte=now).values_list('pk',flat=True):deliver_mail(id)


def deliver_mail(id):
    with transaction.atomic():
        row=object_get(Outbox,id,True)
        if row.state not in ['pending','retry']:return
        row.state='sending';row.lease_until=timezone.now()+timedelta(minutes=2);row.attempts+=1;row.save()
    try:
        require(settings.EMAIL_HOST and settings.DEFAULT_FROM_EMAIL,'email_unconfigured','SMTP eksik.',503)
        delivered=send_mail(row.subject,decrypted_text(row.body),settings.DEFAULT_FROM_EMAIL,[row.destination or row.recipient.email],fail_silently=False);require(delivered==1,'email_failed','SMTP teslimi doğrulanamadı.',503)
    except Exception:
        with transaction.atomic():Outbox.objects.filter(pk=id).update(state='retry',next_at=timezone.now()+timedelta(seconds=min(3600,30*2**min(row.attempts,7))),lease_until=None)
    else:Outbox.objects.filter(pk=id).update(state='sent',lease_until=None)
