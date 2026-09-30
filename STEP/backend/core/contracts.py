from datetime import timedelta
from decimal import ROUND_HALF_UP
from zoneinfo import ZoneInfo
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from .common import *
from .serialization import dto

@transaction.atomic
def contracts(request,id=None,action=None):
    u=request.user;data=request.data
    if not id:
        if request.method=='GET':return page(request,member_contracts(u).order_by('-created_at'),dto)
        fields(data,['application','scope','expected_duration','revision_terms']);app=object_get(Application,data['application'])
        team=object_get(Team,app.team_id,True) if app.team_id else None
        app=object_get(Application,data['application'],True)
        if team:app.team=team
        require(app.job.owner_id==u.pk and app.status=='submitted')
        require(not Contract.objects.filter(application=app).exists(),'already_hired','Teklif için sözleşme zaten var.',409)
        rate=app.price;limit=decimal_hours(data['weekly_limit']) if app.job.work_type=='hourly' else None
        contract=Contract.objects.create(application=app,employer=u,freelancer=app.team.leader if app.team_id else app.student,team=app.team,payee=app.team.leader if app.team_id else app.student,scope=data['scope'],work_type=app.job.work_type,rate=rate,weekly_limit=limit,expected_duration=data['expected_duration'],revision_terms=data['revision_terms'],tracker_required=True if app.job.work_type=='hourly' else bool(data.get('tracker_required',False)))
        replace_workers(contract,data.get('members',[]))
        if contract.work_type=='fixed':create_milestones(contract,data.get('milestones',[]))
        conv=app.conversation;conv.contract=contract;conv.save()
        conv.users.add(*User.objects.filter(pk__in=contract.workers.values_list('user_id',flat=True)))
        app.status='selected';app.save();notify(contract.freelancer,'contract.created','Sözleşme onayınızı bekliyor.',contract);return dto(contract)
    # Team lock precedes the contract lock so leadership approval and the
    # active-contract set cannot change between baseline validation and commit.
    if request.method!='GET':
        team_id=Contract.objects.filter(pk=identity(id)).values_list('team_id',flat=True).first()
        if team_id:object_get(Team,team_id,True)
    contract=object_get(Contract,id,request.method!='GET');contract_access(u,contract,action in ['accept','reoffer','changes','cancel','complete'])
    if action=='reoffer':
        require(u.pk==contract.employer_id and contract.status=='pending' and contract.team_id is not None,'reoffer_scope','Yalnız işveren eski takım lideri sürümündeki bekleyen teklifi yeniden açabilir.',409);fields(data,['reason'])
        require(contract.freelancer_id!=contract.team.leader_id or contract.payee_id!=contract.team.leader_id,'offer_current','Teklifin lider sürümü zaten güncel.',409)
        target_ids=[*contract.milestones.values_list('pk',flat=True),*contract.weeks.values_list('pk',flat=True)]
        require(not Payment.objects.filter(target_id__in=target_ids).exists() and not WorkSession.objects.filter(contract=contract).exists() and not TimeBlock.objects.filter(session__contract=contract).exists() and not ManualTime.objects.filter(contract=contract).exists(),'offer_has_activity','Ödeme denemesi veya çalışma kaydı bulunan teklif yeniden açılamaz.',409)
        ContractChange.objects.create(contract=contract,proposer=u,status='superseded',base_version=contract.version,terms=json_safe({'previous_snapshot':{'freelancer':contract.freelancer_id,'payee':contract.payee_id,'accepted_by':contract.accepted_by,'version':contract.version},'reason':str(data['reason'])}),accepted_by=contract.accepted_by)
        contract.freelancer=contract.team.leader;contract.payee=contract.team.leader;contract.accepted_by=[];contract.version+=1;contract.save();contract.application.conversation.users.add(contract.team.leader);audit(u,contract,str(data['reason']),'contract.reoffer');notify(contract.team.leader,'contract.reoffer','Güncel liderle sözleşme karşılıklı onaya yeniden açıldı.',contract);return dto(contract)
    if action=='accept':
        require(contract.status=='pending','contract_state','Sözleşme onay beklemiyor.',409)
        require(not contract.team_id or (contract.freelancer_id==contract.team.leader_id and contract.payee_id==contract.team.leader_id),'stale_team_leader','Teklifin lider/ödeme alıcısı sürümü değişti; işveren güncel liderle yeni teklif oluşturmalıdır.',409)
        employer(contract.employer)
        for w in contract.workers.filter(active=True).select_related('user'):student(w.user,True)
        require(u.pk==contract.employer_id or u.pk==(contract.team.leader_id if contract.team_id else contract.freelancer_id))
        contract.accepted_by=list(set(contract.accepted_by+[str(u.pk)]))
        if {str(contract.employer_id),str(contract.freelancer_id)}<=set(contract.accepted_by):contract.status='active'
        contract.save();return dto(contract)
    if action=='changes':
        require(contract.status=='active','contract_state','Aktif sözleşme gerekir.',409)
        allowed={'scope','rate','weekly_limit','expected_duration','revision_terms','milestones','members','tracker_required'};terms={k:v for k,v in data.items() if k in allowed}
        require(bool(terms),'change_empty','Değişiklik alanı gerekir.',400)
        change=ContractChange.objects.create(contract=contract,proposer=u,terms=json_safe(terms),accepted_by=[str(u.pk)],base_version=contract.version);return dto(change)
    if action=='cancel':
        require(contract.status in ['pending','active'],'contract_state','Sözleşme iptal edilemez.',409)
        from .payments import queue_refund
        require(not WorkSession.objects.filter(contract=contract,stopped_at=None).exists(),'pending_offline_grants','Senkronizasyonu tamamlanmamış çalışma yetkileri iptalden önce sonuçlandırılmalıdır.',409)
        require(not contract.milestones.filter(status__in=['release_pending','refund_pending']).exists() and not contract.weeks.filter(status__in=['release_pending','refund_pending']).exists(),'pending_money_operation','Devam eden para işlemi uzlaştırılmadan karşıt iade başlatılamaz.',409)
        for target in [*contract.milestones.select_for_update(),*contract.weeks.select_for_update()]:
            if target.status in ['released','refunded','unfunded']:continue
            if isinstance(target,Week):week_totals(target);target.save()
            started=target.status in ['in_progress','submitted','revision','review','disputed'] or (isinstance(target,Week) and target.worked_seconds>0) or (isinstance(target,Milestone) and TimeBlock.objects.filter(session__contract=contract,session__funding__milestone=str(target.pk)).exists())
            if started:
                target.status='disputed';target.save();Dispute.objects.get_or_create(contract=contract,target_type='milestone' if isinstance(target,Milestone) else 'week',target_id=target.pk,status='open',defaults={'opener':u,'reason':data.get('reason','Sözleşme iptali: tamamlanmış/onaysız çalışma')})
            else:queue_refund(target)
        from .payments import cancel_rollover
        cancel_rollover(contract)
        contract.status='cancelled';contract.save();return dto(contract)
    if action=='complete':
        require(contract.status=='active' and not Dispute.objects.filter(contract=contract,status='open').exists() and not contract.milestones.exclude(status__in=['released','refunded']).exists() and not contract.weeks.exclude(status='released').exists(),'open_work','Açık iş/fon/itiraz var.',409)
        ids=set(contract.accepted_by);tag='complete:'+str(u.pk);ids.add(tag);contract.accepted_by=list(ids)
        if {'complete:'+str(contract.employer_id),'complete:'+str(contract.freelancer_id)}<=ids:contract.status='completed'
        contract.save();return dto(contract)
    return dto(contract)

def replace_workers(contract,members):
    if contract.team_id:
        require(isinstance(members,list) and members,'members_required','Takım çalışanları ve ücretleri zorunlu.',400)
    else:members=[{'user':str(contract.freelancer_id),'hourly_rate':str(contract.rate)}]
    unique=set()
    for member in members:
        fields(member,['user','hourly_rate']);u=object_get(User,member['user']);already_working=contract.workers.filter(user=u,active=True).exists();student(u,apply=contract.status=='active' and not already_working)
        require(u.pk not in unique,'duplicate_worker','Çalışan iki kez listelenemez.',400);unique.add(u.pk)
        if contract.team_id:require(contract.team.memberships.filter(user=u,status='active').exists(),'worker_membership','Aktif takım üyesi gerekir.',400)
        ContractWorker.objects.update_or_create(contract=contract,user=u,defaults={'hourly_rate':money(member['hourly_rate']),'active':True})
    removed=ContractWorker.objects.filter(contract=contract,active=True).exclude(user_id__in=unique).values('user_id')
    require(not WorkSession.objects.filter(contract=contract,owner_id__in=removed,stopped_at=None).exists(),'pending_offline_grants','Çalışanın açık kayıt yetkisi senkronize edilmeden çalışan listesi değiştirilemez.',409)
    ContractWorker.objects.filter(contract=contract).exclude(user_id__in=unique).update(active=False)

def create_milestones(contract,items):
    require(isinstance(items,list) and items,'milestones_required','Sabit iş aşamaları zorunlu.',400)
    for item in items:
        fields(item,['title','amount']);Milestone.objects.create(contract=contract,title=item['title'],amount=money(item['amount']))

@transaction.atomic
def change_accept(request,id):
    row=object_get(ContractChange,id,True);c=Contract.objects.select_for_update().get(pk=row.contract_id);contract_access(request.user,c,True)
    require(row.status=='pending' and row.base_version==c.version,'stale_change','Değişiklik artık güncel değil.',409)
    require(request.user.pk!=row.proposer_id,'counterparty_required','Karşı tarafın onayı gerekir.',409)
    terms=row.terms
    for key in ['scope','expected_duration','revision_terms']:
        if key in terms:require(bool(terms[key]),'terms_empty','Koşul boş olamaz.',400);setattr(c,key,terms[key])
    for key in ['rate','weekly_limit']:
        if key in terms:setattr(c,key,money(terms[key]))
    if 'tracker_required' in terms:
        require(isinstance(terms['tracker_required'],bool),'tracker_option','Takip seçimi boolean olmalıdır.',400)
        require(c.work_type!='hourly' or terms['tracker_required'] is True,'hourly_tracker','Saatlik takip zorunludur.',400)
        c.tracker_required=terms['tracker_required']
    if 'members' in terms:replace_workers(c,terms['members'])
    if 'rate' in terms and not c.team_id:
        # Future weeks snapshot the accepted worker rate. Existing Week
        # snapshots remain immutable, and team member rates stay independent.
        updated=c.workers.filter(user_id=c.freelancer_id,active=True).update(hourly_rate=c.rate)
        require(updated==1,'worker_missing','Bireysel sözleşmenin aktif çalışanı bulunamadı.',409)
    if 'milestones' in terms:
        for item in terms['milestones']:
            fields(item,['title','amount'])
            if item.get('id'):
                milestone=object_get(Milestone,item['id'],True);require(milestone.contract_id==c.pk,'milestone_scope','Aşama başka sözleşmeden alınamaz.',400)
                value=money(item['amount'])
                frozen=milestone.status!='unfunded' or Payment.objects.filter(target_type='milestone',target_id=milestone.pk).exists()
                if frozen:require(milestone.title==item['title'] and milestone.amount==value,'funded_terms','Fonlanan aşama geçmişi değiştirilemez.',409)
                else:milestone.title=item['title'];milestone.amount=value;milestone.save()
            else:Milestone.objects.create(contract=c,title=item['title'],amount=money(item['amount']))
    c.version+=1;c.save();row.accepted_by=list(set(row.accepted_by+[str(request.user.pk)]));row.status='accepted';row.save();return dto(row)

@transaction.atomic
def milestones(request,id,action):
    m=object_get(Milestone,id,True);c=Contract.objects.select_for_update().get(pk=m.contract_id);require(c.status=='active','contract_inactive','Aktif sözleşme gerekir.',409)
    if action in ['start','submit']:worker(request.user,c)
    else:require(request.user.pk==c.employer_id)
    if action=='start':require(m.status=='funded','milestone_unfunded','Ön fonlanan aşama gerekir.',409);m.status='in_progress'
    elif action=='submit':
        require(not WorkSession.objects.filter(contract=c,funding__milestone=str(m.pk),stopped_at=None).exists(),'pending_offline_grants','Aşamanın bütün çalışma yetkileri senkronize edilip durdurulmadan teslim edilemez.',409)
        require(m.status in ['funded','in_progress','revision'],'milestone_state','Bu aşama teslim edilemez.',409);fields(request.data,['text'])
        asset_ids=request.data.get('attachment_ids',[])
        for id in asset_ids:
            a=object_get(Asset,id);require(a.contract_id==c.pk and a.owner_id==request.user.pk,'attachment_scope','Teslim dosyası kapsamı yanlış.',400)
        m.revision+=1;m.submission={'text':request.data['text'],'attachment_ids':asset_ids,'revision':m.revision};m.submitted_at=timezone.now();m.review_due_at=m.submitted_at+timedelta(days=14);m.status='submitted';notify(c.employer,'delivery.submitted','Aşama teslim edildi; inceleme dönemi başladı.',m)
    else:
        decision=request.data.get('decision');require(m.status=='submitted','milestone_state','Teslim edilmiş aşama gerekir.',409)
        if decision=='approve':
            from .payments import release_target
            return release_target(m)
        require(decision in ['revision','dispute'],'decision_invalid','Geçerli karar gerekir.',400)
        m.status='revision' if decision=='revision' else 'disputed';m.review_due_at=None
        if decision=='dispute':open_dispute(request.user,c,m,request.data.get('reason','Teslim itirazı'))
        notify(c.freelancer,'delivery.'+decision,'İşveren teslim incelemesini sonuçlandırdı.',m)
    m.save();return dto(m)

def week_bounds(start=None):
    local=(start or timezone.now()).astimezone(ZoneInfo('Europe/Istanbul'));local=local.replace(hour=0,minute=0,second=0,microsecond=0)-timedelta(days=local.weekday());return local,local+timedelta(days=7)

def week_totals(week):
    blocks=TimeBlock.objects.filter(session__contract=week.contract,starts_at__gte=week.starts_at,ends_at__lte=week.ends_at)
    manual=ManualTime.objects.filter(contract=week.contract,status='approved',starts_at__gte=week.starts_at,ends_at__lte=week.ends_at)
    total=0;gross=Decimal('0')
    for row in [*blocks,*manual]:
        seconds=row.seconds if isinstance(row,TimeBlock) else int((row.ends_at-row.starts_at).total_seconds());total+=seconds
        rate=Decimal(str(week.rate_snapshot.get(str(row.owner_id),'0')));require(rate>0,'rate_snapshot','Dönemde kabul edilmiş çalışan ücreti yok.',409);gross+=Decimal(seconds)*rate/Decimal(3600)
    require(total<=int(week.limit_hours*3600),'weekly_limit','Ortak haftalık saat sınırı aşıldı.',409)
    week.worked_seconds=total;week.gross=gross.quantize(CENT,rounding=ROUND_HALF_UP);week.net=(week.gross*Decimal('0.90')).quantize(CENT,rounding=ROUND_HALF_UP)
    return week

@transaction.atomic
def weeks(request,contract_id=None,id=None,action=None):
    if contract_id:
        c=object_get(Contract,contract_id,True);contract_access(request.user,c)
        if request.method=='GET':return page(request,c.weeks.order_by('-starts_at'),dto)
        require(request.user.pk==c.employer_id and c.status=='active' and c.work_type=='hourly');start,end=week_bounds(instant(request.data['starts_at']) if request.data.get('starts_at') else None)
        require(end>timezone.now(),'period_past','Geçmiş hafta fonlanamaz.',400)
        choice=request.data.get('remainder_choice','refund');require(choice in ['refund','rollover'],'remainder_invalid','Fon seçimi gerekir.',400)
        rates={str(w.user_id):str(w.hourly_rate) for w in c.workers.filter(active=True)};require(bool(rates),'worker_missing','Çalışan yok.',409)
        reserve=money((max(map(Decimal,rates.values()))*c.weekly_limit).quantize(CENT,rounding=ROUND_HALF_UP))
        row,created=Week.objects.get_or_create(contract=c,starts_at=start,defaults={'ends_at':end,'limit_hours':c.weekly_limit,'reserved_amount':reserve,'remainder_choice':choice,'rate_snapshot':rates})
        require(created,'week_exists','Bu dönem zaten var.',409);return dto(row)
    row=object_get(Week,id,True);c=Contract.objects.select_for_update().get(pk=row.contract_id);require(request.user.pk==c.employer_id)
    if action=='close':
        require(row.status=='funded' and timezone.now()>=row.ends_at,'period_not_ended','Haftalık dönem henüz bitmedi.',409)
        require(not WorkSession.objects.filter(contract=c,created_at__gte=row.starts_at,created_at__lt=row.ends_at,stopped_at=None).exists(),'pending_offline_grants','Senkronizasyonu bitmemiş çalışma yetkileri var; destek incelemesi gerekir.',409)
        require(not ManualTime.objects.filter(contract=c,status='pending',starts_at__gte=row.starts_at,ends_at__lte=row.ends_at).exists(),'pending_manual_review','Bekleyen manuel süre onay veya ret ile sonuçlandırılmalıdır.',409)
        week_totals(row);row.status='review';row.review_due_at=timezone.now()+timedelta(days=5);row.save();notify(c.freelancer,'week.review','Haftalık ödeme inceleme döneminde.',row)
    elif action=='review':
        require(row.status=='review','week_state','Hafta incelemede değil.',409);choice=request.data.get('decision')
        if choice=='approve':
            from .payments import release_target
            return release_target(row)
        require(choice=='dispute','decision_invalid','Geçerli karar gerekir.',400);open_dispute(request.user,c,row,request.data.get('reason','Saatlik itiraz'));row.status='disputed';row.review_due_at=None;row.save()
    return dto(row)

def overlap(user,start,end,exclude=None):
    blocks=TimeBlock.objects.filter(owner=user,starts_at__lt=end,ends_at__gt=start)
    manual=ManualTime.objects.filter(owner=user,status__in=['pending','approved'],starts_at__lt=end,ends_at__gt=start)
    if exclude:manual=manual.exclude(pk=exclude)
    require(not blocks.exists() and not manual.exists(),'time_overlap','Aynı süre birden fazla kayıtta kullanılamaz.',409)

@transaction.atomic
def manual_time(request,contract_id=None,id=None):
    if contract_id:
        if request.method!='GET':User.objects.select_for_update(no_key=True).get(pk=request.user.pk)
        c=object_get(Contract,contract_id,True);contract_access(request.user,c)
        if request.method=='GET':return page(request,ManualTime.objects.filter(contract=c).order_by('-created_at'),dto)
        worker(request.user,c);require(c.status=='active' and c.work_type=='hourly','contract_state','Aktif saatlik sözleşme gerekir.',409)
        User.objects.select_for_update(no_key=True).get(pk=request.user.pk);fields(request.data,['starts_at','ends_at','memo']);start,end=instant(request.data['starts_at']),instant(request.data['ends_at']);require(end>start and end<=timezone.now(),'time_invalid','Geçerli geçmiş süre gerekir.',400);overlap(request.user,start,end)
        week=Week.objects.select_for_update().filter(contract=c,starts_at__lte=start,ends_at__gte=end,status='funded').first();require(week is not None,'period_unfunded','Ön fonlanan açık hafta gerekir.',409)
        row=ManualTime.objects.create(owner=request.user,contract=c,starts_at=start,ends_at=end,memo=request.data['memo']);return dto(row)
    pending=object_get(ManualTime,id);User.objects.select_for_update(no_key=True).get(pk=pending.owner_id)
    c=object_get(Contract,pending.contract_id,True);row=object_get(ManualTime,id,True);require(request.user.pk==c.employer_id and row.status=='pending')
    User.objects.select_for_update(no_key=True).get(pk=row.owner_id);choice=request.data.get('decision');require(choice in ['approve','reject'],'decision_invalid','Geçerli karar gerekir.',400)
    if choice=='approve':
        overlap(row.owner,row.starts_at,row.ends_at,row.pk);week=Week.objects.select_for_update().filter(contract=c,starts_at__lte=row.starts_at,ends_at__gte=row.ends_at,status='funded').first();require(week is not None,'period_closed','Dönem ücretlendirmeye kapalı.',409)
        outstanding=sum(s.reserved_seconds-s.used_seconds for s in WorkSession.objects.filter(contract=c,created_at__gte=week.starts_at,created_at__lt=week.ends_at,stopped_at=None))
        week_totals(week);seconds=int((row.ends_at-row.starts_at).total_seconds());require(week.worked_seconds+outstanding+seconds<=int(week.limit_hours*3600),'weekly_limit','Ortak limit çalışma yetkileriyle dolu.',409)
    row.status='approved' if choice=='approve' else 'rejected';row.save();return dto(row)

def open_dispute(user,contract,target,reason):
    kind='milestone' if isinstance(target,Milestone) else 'week'
    row,_=Dispute.objects.get_or_create(contract=contract,target_type=kind,target_id=target.pk,status='open',defaults={'opener':user,'reason':reason})
    target.status='disputed';target.review_due_at=None;target.save();notify(contract.employer,'dispute.open','Ödeme itiraz nedeniyle bekletiliyor.',row);notify(contract.freelancer,'dispute.open','Ödeme itiraz nedeniyle bekletiliyor.',row);return row

@transaction.atomic
def disputes(request,id=None):
    if id:
        row=object_get(Dispute,id,True);investigation(request.user,row.contract,row.pk,'dispute')
        require(row.status=='open','dispute_closed','İtiraz kapalı.',409);choice=request.data.get('decision');fields(request.data,['reason']);target=object_get(Milestone if row.target_type=='milestone' else Week,row.target_id,True)
        require(choice in ['release','refund'],'decision_invalid','Geçerli karar gerekir.',400)
        from .payments import release_target,queue_refund
        if choice=='release':release_target(target,dispute_resolution=True)
        else:queue_refund(target)
        row.status='resolved';row.resolved_at=timezone.now();row.save();audit(request.user,row,request.data['reason'],choice);return dto(row)
    if request.method=='GET':return page(request,Dispute.objects.filter(contract__in=member_contracts(request.user)).order_by('-created_at'),dto)
    fields(request.data,['contract','reason']);c=object_get(Contract,request.data['contract'],True);contract_access(request.user,c,True)
    require(bool(request.data.get('milestone'))!=bool(request.data.get('week')),'dispute_target','Bir ödeme hedefi gerekir.',400)
    target=object_get(Milestone if request.data.get('milestone') else Week,request.data.get('milestone') or request.data['week'],True);require(target.contract_id==c.pk and target.status in ['funded','in_progress','submitted','revision','review','disputed'],'dispute_state','Bu ödeme için itiraz açılamaz.',409)
    return dto(open_dispute(request.user,c,target,request.data['reason']))

def investigation(user,contract,case_id=None,case_type=None):
    require(user.is_staff,'operator_required','İnceleme operatörü gerekir.')
    rows=InvestigationGrant.objects.filter(operator=user,contract=contract,expires_at__gt=timezone.now())
    if case_type:require(user.is_superuser or user.has_perm('core.change_'+('privacyrequest' if case_type=='privacy' else 'dispute')),'operator_permission','İlgili dosya karar yetkisi gerekir.')
    if case_id:rows=rows.filter(case_id=case_id,case_type=case_type)
    require(rows.exists(),'investigation_scope','Bu dosya için atanmış inceleme yetkisi gerekir.')
