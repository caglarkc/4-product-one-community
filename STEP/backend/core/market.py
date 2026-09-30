from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .common import *
from .serialization import dto

@transaction.atomic
def jobs(request,id=None,action=None):
    u=request.user;data=request.data
    if id:
        row=object_get(Job,id,request.method!='GET')
        if request.method=='GET':
            require(row.status=='open' or (u.is_authenticated and row.owner_id==u.pk),'not_found','İlan bulunamadı.',404);return dto(row,u)
        require(row.owner_id==u.pk)
        if action=='publish' or (request.method=='PATCH' and data.get('publish')):
            publish(u,row);return dto(row,u)
        if action=='cancel':
            require(row.status in ['open','draft'],'job_state','İlan iptal edilemez.',409)
            # Contract cancellation remains separate; credits cannot erase work-money obligations.
            row.status='cancelled';row.save();refund_job(row)
            return dto(row,u)
        allowed=['title','description','category','skills','budget','expected_duration','deadline']
        for key in allowed:
            if key in data:setattr(row,key,instant(data[key]) if key=='deadline' and data[key] else (money(data[key]) if key=='budget' else (object_get(Category,data[key]) if key=='category' else data[key])))
        validate_job(row);row.save();return dto(row,u)
    if request.method=='GET':
        rows=Job.objects.order_by('-created_at')
        mine=request.query_params.get('mine','').lower() in ['1','true']
        require(not mine or u.is_authenticated,'authentication_required','Kendi ilanlarınız için giriş gerekir.',401)
        rows=rows.filter(owner=u) if mine else rows.filter(status='open')
        for key in ['category','work_type']:
            if request.query_params.get(key):rows=rows.filter(**{('category_id' if key=='category' else key):request.query_params[key]})
        if request.query_params.get('q'):rows=rows.filter(Q(title__icontains=request.query_params['q'])|Q(description__icontains=request.query_params['q']))
        return page(request,rows,lambda row:dto(row,u))
    employer(u);fields(data,['title','description','category','skills','work_type','budget','expected_duration'])
    row=Job.objects.create(owner=u,title=data['title'],description=data['description'],category=object_get(Category,data['category']),skills=data['skills'],work_type=data['work_type'],budget=money(data['budget']),expected_duration=data['expected_duration'],deadline=instant(data['deadline']) if data.get('deadline') else None)
    validate_job(row)
    if data.get('publish'):publish(u,row)
    return dto(row,u)

def validate_job(row):
    require(row.work_type in ['fixed','hourly'],'work_type','Geçerli iş türü gerekir.',400)
    require(Category.objects.filter(pk=row.category_id).exists(),'category_invalid','Yönetim kategorisi gerekir.',400)
    require(isinstance(row.skills,list) and row.skills,'skills_invalid','Beceri listesi gerekir.',400)
    require(bool(row.title and row.description and row.expected_duration),'missing_fields','İlan alanları zorunlu.',400)
    require(not row.deadline or row.deadline>timezone.now(),'deadline_past','Başvuru son tarihi gelecekte olmalıdır.',400)

def publish(user,row):
    employer(user);require(row.status=='draft','job_state','Yalnız taslak yayınlanabilir.',409)
    credit_change(wallet_for(user),-int(setting_value('post_cost')),'post','post:'+str(row.pk),row.pk)
    row.status='open';row.save();notify(user,'job.published','İlan yayımlandı.',row)

def refund_job(job):
    # Once a contract exists, cancellation credit details require an operator case.
    if Contract.objects.filter(application__job=job).exists():return
    sources=[job.pk,*job.applications.values_list('pk',flat=True)]
    for entry in CreditEntry.objects.filter(source__in=sources,amount__lt=0,reason__in=['post','application']):
        credit_change(entry.wallet,-entry.amount,'job_refund','job-refund:'+str(entry.pk),entry.source)
    for promotion in Promotion.objects.select_for_update().filter(target_type='job',target_id=job.pk,refunded=False):
        elapsed=(promotion.ends_at-promotion.created_at).total_seconds();remaining=max(0,(promotion.ends_at-timezone.now()).total_seconds())
        amount=int(Decimal(promotion.credits)*Decimal(str(remaining/elapsed))) if elapsed>0 else 0
        if amount:credit_change(promotion.wallet,amount,'boost_refund','boost-refund:'+str(promotion.pk),job.pk)
        promotion.refunded=True;promotion.save()

@transaction.atomic
def applications(request,id=None,job_id=None,action=None):
    u=request.user;data=request.data
    if id:
        row=object_get(Application,id,request.method!='GET')
        own=(row.team.leader_id==u.pk) if row.team_id else row.student_id==u.pk
        if action=='reject':require(row.job.owner_id==u.pk)
        else:require(own or (request.method=='GET' and row.job.owner_id==u.pk))
        require(row.status=='submitted','application_state','Seçimden sonra teklif değiştirilemez.',409)
        if action in ['withdraw','reject']:
            row.status='withdrawn' if action=='withdraw' else 'rejected';row.save();notify(row.student,'proposal.'+row.status,'Teklif durumu değişti.',row);return dto(row,u)
        for key in ['cover_letter','price','duration','sample_url']:
            if key in data:setattr(row,key,money(data[key]) if key=='price' else (safe_url(data[key]) if key=='sample_url' and data[key] else data[key]))
        fields({'cover_letter':row.cover_letter,'duration':row.duration},['cover_letter','duration']);row.save();return dto(row,u)
    if request.method=='GET':
        rows=Application.objects.filter(Q(student=u)|Q(team__leader=u)).distinct().order_by('-created_at')
        if job_id:
            job=object_get(Job,job_id)
            if job.owner_id==u.pk:rows=Application.objects.filter(job=job).order_by('-created_at')
            else:rows=rows.filter(job=job)
        return page(request,rows,lambda row:dto(row,u))
    job=object_get(Job,job_id,True);student(u,True);require(job.owner_id!=u.pk,'self_apply','Kendi ilanınıza başvuramazsınız.',400)
    require(job.status=='open' and (not job.deadline or job.deadline>timezone.now()),'job_closed','İlan başvurulara kapalı.',409)
    fields(data,['cover_letter','price','duration']);team=object_get(Team,data['team']) if data.get('team') else None
    if team:team_access(u,team,True)
    require(not Application.objects.filter(job=job,team=team,**({} if team else {'student':u})).exists(),'duplicate_proposal','Bu ilan için teklif zaten var.',409)
    invited=Invitation.objects.filter(job=job,status='pending',**({'team':team} if team else {'student':u})).first()
    conv=invited.conversation if invited else Conversation.objects.create();conv.users.add(u,job.owner)
    row=Application.objects.create(job=job,student=u,team=team,cover_letter=data['cover_letter'],price=money(data['price']),duration=data['duration'],sample_url=safe_url(data['sample_url']) if data.get('sample_url') else '',conversation=conv)
    if invited:
        row.conversation=invited.conversation;row.save();invited.status='accepted';invited.save()
    else:credit_change(wallet_for(u,team,True),-int(setting_value('apply_cost')),'application','apply:'+str(row.pk),row.pk)
    notify(job.owner,'proposal.submitted','Yeni teklif geldi.',row);return dto(row,u)

@transaction.atomic
def invitations(request,job_id=None,id=None):
    u=request.user;data=request.data
    if id:
        row=object_get(Invitation,id,True);require(row.student_id==u.pk or (row.team_id and row.team.leader_id==u.pk));row.status='declined';row.save();return dto(row,u)
    if request.method=='GET':
        rows=Invitation.objects.filter(job__owner=u) if request.query_params.get('sent','').lower() in ['true','1'] else Invitation.objects.filter(Q(student=u)|Q(team__leader=u))
        return page(request,rows.distinct().order_by('-created_at'),dto)
    job=object_get(Job,job_id,True);require(job.owner_id==u.pk and job.status=='open');require(bool(data.get('student'))!=bool(data.get('team')),'invitation_target','Tek hedef gerekir.',400)
    team=object_get(Team,data['team']) if data.get('team') else None;target=team.leader if team else object_get(User,data['student']);student(target)
    conv=Conversation.objects.create();conv.users.add(u,target)
    row=Invitation.objects.create(job=job,student=None if team else target,team=team,conversation=conv);notify(target,'invitation','İş daveti geldi.',row);return dto(row,u)

@transaction.atomic
def teams(request,id=None,action=None):
    u=request.user;data=request.data
    if not id:
        if request.method=='GET':return page(request,Team.objects.filter(memberships__user=u,memberships__status='active').order_by('-created_at'),lambda row:dto(row,u))
        student(u);fields(data,['name']);row=Team.objects.create(leader=u,name=data['name'],description=data.get('description',''));Membership.objects.create(team=row,user=u,status='active');wallet_for(u,row,True);return dto(row,u)
    row=object_get(Team,id,request.method!='GET')
    if action=='membership':
        member=Membership.objects.select_for_update().filter(team=row,user=u).first();require(member is not None)
        choice=data.get('action');require(choice in ['accept','decline','leave'],'action_invalid','Geçerli üyelik işlemi gerekir.',400)
        if choice=='accept':require(member.status=='invited','membership_state','Bekleyen davet gerekir.',409);member.status='active'
        elif choice=='leave':require(row.leader_id!=u.pk,'leader_leave','Önce lider değişikliği gerekir.',409);member.status='left'
        else:member.status='declined'
        member.save();return dto(row,u) if member.status=='active' else {'id':row.pk,'name':row.name,'description':row.description,'leader_name':row.leader.display_name,'membership_status':member.status}
    team_access(u,row,request.method!='GET')
    if action=='invite':
        fields(data,['email']);target=User.objects.filter(email=data['email'].casefold()).first();require(target is not None,'user_missing','Kayıtlı öğrenci hesabı gerekir.',404);student(target)
        member,created=Membership.objects.get_or_create(team=row,user=target)
        require(created or member.status!='active','already_member','Üye zaten takımda.',409);member.status='invited';member.save();notify(target,'team.invitation','Takım daveti geldi.',row);return dto(row,u)
    if action=='leader-change':
        fields(data,['new_leader','payee','reason']);require(isinstance(data.get('contract_ids'),list),'contract_ids','Aktif sözleşme kimlik listesi gerekir.',400);target=object_get(User,data['new_leader']);payee=object_get(User,data['payee'])
        require(row.memberships.filter(user=target,status='active').exists(),'leader_member','Yeni lider aktif üye olmalıdır.',400)
        require(payee.pk in {target.pk,row.leader_id},'payee_leader','Mevcut veya yeni lider ödeme alıcısı açıkça belirlenmelidir.',400)
        contracts=list(Contract.objects.select_for_update().filter(team=row,status='active').order_by('pk'))
        require(set(map(str,data['contract_ids']))=={str(c.pk) for c in contracts},'contracts_incomplete','Bütün aktif sözleşmeler açıkça seçilmelidir.',409)
        change=LeaderChange.objects.create(team=row,baseline_leader=row.leader,new_leader=target,payee=payee,reason=data['reason']);change.contracts.set(contracts);return dto(change)
    if request.method=='PATCH':
        for key in ['name','description']:
            if key in data:setattr(row,key,data[key])
        row.save()
    return dto(row,u)

@transaction.atomic
def leader_approve(request,id):
    u=request.user;row=object_get(LeaderChange,id)
    # The same Team -> dependent record -> Contract order is used when a
    # contract becomes active or leaves the active set. Never approve against
    # an old leader or an incomplete, independently changing employer set.
    team=object_get(Team,row.team_id,True);row=object_get(LeaderChange,id,True)
    require(row.status=='pending','change_state','Değişiklik beklemiyor.',409)
    current=list(Contract.objects.select_for_update().filter(team=team,status='active').order_by('pk'))
    baseline=set(row.contracts.values_list('pk',flat=True))
    require(team.leader_id==row.baseline_leader_id and baseline=={c.pk for c in current},'stale_leader_change','Lider veya aktif sözleşmeler değişti; bütün güncel işverenler için yeni lider değişim isteği oluşturulmalıdır.',409)
    require(team.memberships.filter(user=row.new_leader,status='active').exists(),'leader_member','Yeni lider hâlâ aktif takım üyesi olmalıdır.',409)
    require(row.payee_id in {row.baseline_leader_id,row.new_leader_id},'payee_leader','Ödeme alıcısı kabul edilen mevcut veya yeni lider olmalıdır.',409)
    employers={str(c.employer_id) for c in current}
    require(u.is_staff or str(u.pk) in employers)
    if u.is_staff:
        require(u.is_superuser or u.has_perm('core.change_leaderchange'),'operator_permission','Lider değişimi yönetim onayı yetkisi gerekir.');row.admin_approved=True;audit(u,row,'Lider ve ödeme alıcısı kimliği onayı','approve')
    else:row.accepted_by=list(set(row.accepted_by+[str(u.pk)]))
    if row.admin_approved and employers<=set(row.accepted_by):
        team.leader=row.new_leader;team.save()
        for contract in current:
            contract.freelancer=row.new_leader;contract.payee=row.payee;contract.version+=1;contract.save()
            contract.application.conversation.users.add(row.new_leader)
        row.status='approved'
    row.save();return dto(row,u)

@transaction.atomic
def boost(request):
    u=request.user;data=request.data;fields(data,['target_type','target_id','duration_option'])
    require(data['target_type'] in ['job','application'],'boost_type','Geçerli hedef gerekir.',400)
    target=object_get(Job if data['target_type']=='job' else Application,data['target_id'],True)
    if isinstance(target,Job):require(target.owner_id==request.user.pk and target.status=='open');team=None
    else:require(target.status=='submitted');team=target.team;require(team.leader_id==request.user.pk if team else target.student_id==request.user.pk)
    hours=int(setting_value('boost_hours'));require(str(data['duration_option'])==str(hours),'boost_duration','Yalnız yapılandırılmış süre seçilebilir.',400)
    count=int(setting_value('boost_cost'));wallet=wallet_for(request.user,team,True)
    row=Promotion.objects.create(target_type=data['target_type'],target_id=target.pk,wallet=wallet,credits=count,ends_at=timezone.now()+timedelta(hours=hours));credit_change(wallet,-count,'boost','boost:'+str(row.pk),target.pk);target.boosted_until=row.ends_at;target.save();return dto(row,u)
