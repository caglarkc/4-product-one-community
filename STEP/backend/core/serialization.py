from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import *
from .common import json_safe, policy, job_asset_access

def profile(user):
    allowed = {key:user.profile.get(key) for key in ['university','department','bio','skills','hourly_rate','photo','portfolio_links']}
    return {'id':str(user.pk),'user':str(user.pk),'display_name':user.display_name,**allowed}

def user_dto(user):
    e = Eligibility.objects.filter(user=user).first()
    v = EmployerVerification.objects.filter(user=user).first()
    return {'id':user.pk,'email':user.email,'display_name':user.display_name,'roles':user.roles,'is_staff':user.is_staff,'profile':profile(user),'preferences':{'in_app':user.preferences.get('in_app',True),'email':user.preferences.get('email',True)},'verification':{'student':{'status':e.status if e else 'unverified','student_email':e.student_email if e else '', 'verified_until':e.verified_until if e else None},'employer':{'status':v.status if v else 'unverified','kind':v.kind if v else 'individual','phone_verified':bool(v and v.phone_verified_at)},'payment':{'status':'onboarded' if user.submerchant_key else 'unavailable','provider_ready':bool(user.submerchant_key)}}}

def bank_transfer_proven(payout):
    if payout.mode!='iyzico_live' or payout.status!='paid' or not payout.bank_digest:return False
    proofs=list(BankSettlement.objects.filter(payout=payout).select_related('payment'))
    return bool(proofs) and all(proof.bank_digest==payout.bank_digest and proof.amount>0 and proof.payment.mode==payout.mode for proof in proofs) and sum((proof.amount for proof in proofs),Decimal('0'))==payout.amount

def dto(row,viewer=None):
    base = {'id':row.pk,'created_at':row.created_at}
    if isinstance(row,User): return profile(row)
    if isinstance(row,University): return {**base,'name':row.name,'domains':row.domains}
    if isinstance(row,Category): return {**base,'name':row.name,'slug':row.name.lower().replace(' ','-')}
    if isinstance(row,Job): return {**base,'owner':row.owner_id,'owner_name':row.owner.display_name,'category':row.category_id,'category_name':row.category.name,**{k:getattr(row,k) for k in ['title','description','skills','work_type','budget','expected_duration','deadline','status','boosted_until']},'attachments':[dto(a) for a in Asset.objects.filter(job=row,purged_at=None)] if job_asset_access(viewer,row) else []}
    if isinstance(row,Application): return {**base,'job':row.job_id,'student':row.student_id,'student_name':row.student.display_name,'team':row.team_id,'team_name':row.team.name if row.team_id else None,'job_title':row.job.title,'conversation':row.conversation_id,**{k:getattr(row,k) for k in ['cover_letter','price','duration','sample_url','status','boosted_until']}}
    if isinstance(row,Invitation): return {**base,'job':row.job_id,'student':row.student_id,'student_name':row.student.display_name if row.student_id else None,'team':row.team_id,'team_name':row.team.name if row.team_id else None,'job_title':row.job.title,'status':row.status,'conversation':row.conversation_id}
    if isinstance(row,Team): return {**base,'name':row.name,'description':row.description,'leader':row.leader_id,'wallet_id':getattr(getattr(row,'wallet',None),'pk',None),'active_contract_ids':list(Contract.objects.filter(team=row,status='active').values_list('pk',flat=True)) if viewer and viewer.pk==row.leader_id else [],'members':[{'user':m.user_id,'display_name':m.user.display_name,'status':m.status} for m in row.memberships.select_related('user')],'leader_changes':[dto(c) for c in LeaderChange.objects.filter(team=row)]}
    if isinstance(row,Contract): return {**base,'stale_team_leader':bool(row.team_id and row.status=='pending' and (row.freelancer_id!=row.team.leader_id or row.payee_id!=row.team.leader_id)),'current_team_leader':{'id':row.team.leader_id,'display_name':row.team.leader.display_name} if row.team_id else None,'job':row.application.job_id,'application':row.application_id,'job_title':row.application.job.title,'student_name':row.freelancer.display_name,'team_name':row.team.name if row.team_id else None,'employer':row.employer_id,'freelancer':row.freelancer_id,'team':row.team_id,'payee':row.payee_id,**{k:getattr(row,k) for k in ['status','scope','work_type','rate','weekly_limit','expected_duration','revision_terms','tracker_required','accepted_by']},'members':[{'user':w.user_id,'display_name':w.user.display_name,'hourly_rate':w.hourly_rate} for w in row.workers.filter(active=True)],'milestones':[dto(m) for m in row.milestones.all()],'conversation':row.application.conversation_id,'changes':[dto(c) for c in ContractChange.objects.filter(contract=row)],'leader_changes':[dto(c) for c in LeaderChange.objects.filter(contracts=row)]}
    if isinstance(row,ContractChange): return {**base,'contract':row.contract_id,'proposer':row.proposer_id,'terms':row.terms,'accepted_by':row.accepted_by,'status':row.status}
    if isinstance(row,LeaderChange): return {**base,'team':row.team_id,'baseline_leader':row.baseline_leader_id,'new_leader':row.new_leader_id,'new_leader_name':row.new_leader.display_name,'payee':row.payee_id,'payee_name':row.payee.display_name,'contract_ids':list(row.contracts.values_list('pk',flat=True)),'approved_by':row.accepted_by,'admin_approved':row.admin_approved,'status':row.status,'reason':row.reason}
    if isinstance(row,Milestone):
        submission={**row.submission,'attachments':[dto(a) for a in Asset.objects.filter(pk__in=row.submission.get('attachment_ids',[]),contract=row.contract,captured_at=None,purged_at=None)]} if row.submission else None
        return {**base,'contract':row.contract_id,**{k:getattr(row,k) for k in ['title','amount','status','submitted_at','review_due_at']},'submission':submission}
    if isinstance(row,Week): return {**base,'contract':row.contract_id,**{k:getattr(row,k) for k in ['starts_at','ends_at','status','limit_hours','reserved_amount','worked_seconds','gross','net','review_due_at','remainder_choice']}}
    if isinstance(row,Payment): return {**base,'mode':row.mode,'target_type':row.target_type,'target_id':row.target_id,'amount':row.amount,'currency':'TRY','status':row.status,'checkout_url':row.checkout_url or None,'checkout_expires_at':row.checkout_expires_at,'provider_reference':row.provider_reference or None,'funded_at':row.funded_at,'released_amount':row.released_amount,'refunded_amount':row.refunded_amount,'settlement_status':row.settlement_status,'error_code':row.error_code or None,'attempt':row.attempt,'retry_allowed':row.retry_allowed}
    if isinstance(row,Payout): return {**base,'bank_transfer_proven':bank_transfer_proven(row),'mode':row.mode,'amount':row.amount,'currency':'TRY','account_name':row.account_name,'iban_masked':row.iban_masked,'status':row.status,'reserved_amount':row.amount if row.status in ['requested','processing','unavailable'] else '0.00','provider_reference':row.provider_reference or None,'requested_at':row.created_at,'paid_at':row.paid_at,'failure_reason':row.failure_reason or None}
    if isinstance(row,CreditEntry): return {**base,'delta':row.amount,'balance_after':row.balance_after,'kind':row.reason,'reference':row.source}
    if isinstance(row,Wallet): return {**base,'team':row.team_id,'balance':row.balance,'mode':row.mode,'entries':[dto(e) for e in row.entries.order_by('-created_at')[:100]]}
    if isinstance(row,CreditPurchase): return {**base,'wallet':row.wallet_id,'credits':row.credits,'amount':row.amount,'status':row.status,'payment':p.pk if (p:=Payment.objects.filter(target_type='credit_purchase',target_id=row.pk).first()) else None}
    if isinstance(row,Promotion): return {**base,'target_type':row.target_type,'target_id':row.target_id,'credits':row.credits,'starts_at':row.created_at,'ends_at':row.ends_at,'status':'refunded' if row.refunded else ('active' if row.ends_at>timezone.now() else 'expired')}
    if isinstance(row,Asset): return {'id':row.pk,'name':row.filename,'size':row.size,'mime':row.mime}
    if isinstance(row,TimeBlock):
        a = row.screenshot
        image = {'id':a.pk,'state':a.state,'captured_at':a.captured_at,'publication_ready_at':a.publication_ready_at,'review_due_at':a.publish_at,'privacy_request':getattr(getattr(a,'privacyrequest',None),'pk',None)} if a and a.purged_at is None else None
        return {**base,'client_id':row.client_id,'session':row.session_id,'contract':row.session.contract_id,'owner':row.owner_id,'owner_name':row.owner.display_name,'memo':row.session.memo,**{k:getattr(row,k) for k in ['starts_at','ends_at','seconds','key_count','mouse_count','active_app']},'screenshot':image}
    if isinstance(row,ManualTime): return {**base,'owner':row.owner_id,'owner_name':row.owner.display_name,'starts_at':row.starts_at,'ends_at':row.ends_at,'seconds':int((row.ends_at-row.starts_at).total_seconds()),'memo':row.memo,'status':row.status}
    if isinstance(row,WorkSession): return {'id':row.pk,'contract':row.contract_id,'client_id':row.client_id,'started_at':row.created_at,'mode':settings.STEP_MODE,'reserved_seconds':row.reserved_seconds,'used_seconds':row.used_seconds,'authorized_until':row.ends_at,'funding':row.funding}
    if isinstance(row,Conversation):
        app = Application.objects.filter(conversation=row).first()
        inv = Invitation.objects.filter(conversation=row).first()
        job = app.job if app else (inv.job if inv else (row.contract.application.job if row.contract_id else None))
        return {**base,'job':job.pk if job else None,'contract':row.contract_id,'title':job.title if job else 'STEP görüşmesi','participants':[{'id':u.pk,'display_name':u.display_name} for u in row.users.all()],'updated_at':row.messages.order_by('-created_at').values_list('created_at',flat=True).first() or row.created_at}
    if isinstance(row,Message): return {**base,'sender':row.sender_id,'sender_name':row.sender.display_name,'text':row.text,'attachments':[dto(a) for a in row.attachments.all()]}
    if isinstance(row,Notification): return {**base,'title':'STEP','body':row.text,'event':row.kind,'resource_type':row.kind.split('.')[0],'resource_id':row.resource_id,'read_at':row.read_at}
    if isinstance(row,Rating): return {**base,'author':row.author_id,'party':row.party,'score':row.score,'comment':row.comment}
    if isinstance(row,AuditEvent): return {**base,'actor':row.actor_id,'action':row.outcome,'resource_type':row.resource,'resource_id':row.resource_id,'reason':row.reason}
    if isinstance(row,Report): return {**base,'status':row.status,'reason':row.reason,'job':row.job_id,'job_title':row.job.title,'reporter':row.reporter_id}
    if isinstance(row,Dispute): return {**base,'status':row.status,'reason':row.reason,'contract':row.contract_id,row.target_type:row.target_id,'opened_by':row.opener_id}
    if isinstance(row,PrivacyRequest): return {**base,'status':row.status,'reason':row.reason,'screenshot':row.asset_id,'contract':row.asset.contract_id,'owner':row.asset.owner_id,'owner_name':row.asset.owner.display_name}
    if isinstance(row,RefundRequest): return {**base,'status':row.status,'reason':row.reason,'purchase':row.purchase_id,'wallet':row.purchase.wallet_id,'credits':row.purchase.credits}
    if isinstance(row,EmployerVerification): return {**base,'status':row.status,'reason':'','user':row.user_id,'display_name':row.user.display_name,'kind':row.kind,'phone_verified':bool(row.phone_verified_at),'legal_name':row.details.get('legal_name',''),'company_name':row.details.get('company_name','')}
    raise TypeError('Unspecified DTO: '+row.__class__.__name__)
