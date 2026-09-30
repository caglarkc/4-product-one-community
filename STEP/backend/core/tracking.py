import hashlib
import io
import json
import re
import secrets
from datetime import timedelta
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from django.utils import timezone
from .common import *
from .contracts import overlap,week_totals,investigation
from .serialization import dto


def save_asset(user,upload,contract=None,conversation=None,job=None,screenshot=False,captured_at=None):
    require(upload is not None,'file_required','Dosya gerekir.',400);require(upload.size<=settings.UPLOAD_MAX_BYTES,'file_too_large','Dosya boyutu sınırı aşıldı.',400)
    data=upload.read();upload.seek(0);name=Path(upload.name).name[:180];require(name not in ['','.','..'],'filename_invalid','Geçerli dosya adı gerekir.',400)
    extension=Path(name).suffix.lower();allowed={'.pdf':'application/pdf','.txt':'text/plain','.zip':'application/zip','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}
    require(extension in allowed,'file_type','Dosya türü desteklenmiyor.',400);mime=allowed[extension]
    if screenshot or extension in ['.png','.jpg','.jpeg','.webp']:
        try:
            with Image.open(io.BytesIO(data)) as image:
                image.verify();kind=image.format
        except (UnidentifiedImageError,ValueError,OSError,Image.DecompressionBombError):raise Problem('image_invalid','Geçerli görüntü gerekir.')
        require(kind in ['PNG','JPEG','WEBP'] and (not screenshot or kind=='PNG'),'image_type','Takip görüntüsü PNG olmalıdır.',400)
    elif extension=='.pdf':require(data.startswith(b'%PDF-'),'file_type','PDF içeriği geçersiz.',400)
    elif extension=='.zip':require(data.startswith(b'PK'),'file_type','ZIP içeriği geçersiz.',400)
    else:
        try:data.decode('utf-8')
        except UnicodeDecodeError:raise Problem('file_type','UTF-8 metin gerekir.')
    key=secrets.token_hex(32);settings.PRIVATE_ROOT.mkdir(parents=True,exist_ok=True);path=settings.PRIVATE_ROOT/key
    import os
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as file:file.write(data)
    return Asset.objects.create(owner=user,contract=contract,conversation=conversation,job=job,storage_key=key,filename=name,mime=mime,size=len(data),digest=hashlib.sha256(data).hexdigest(),state='preview' if screenshot else 'private',captured_at=captured_at)

def pending_case(user,asset):
    if not user.is_staff or not asset.contract_id:return False
    grants=InvestigationGrant.objects.filter(operator=user,contract=asset.contract,expires_at__gt=timezone.now())
    for grant in grants:
        if grant.case_type=='privacy' and (user.is_superuser or user.has_perm('core.change_privacyrequest')) and PrivacyRequest.objects.filter(pk=grant.case_id,asset=asset,status='pending').exists():return True
        if grant.case_type=='dispute' and (user.is_superuser or user.has_perm('core.change_dispute')):
            dispute=Dispute.objects.filter(pk=grant.case_id,contract=asset.contract,status='open').first()
            if dispute and TimeBlock.objects.filter(screenshot=asset,**{'session__funding__'+dispute.target_type:str(dispute.target_id)}).exists():return True
    return False

def pending_milestone_attachment(user,asset):
    if not user.is_staff or not asset.contract_id or asset.captured_at is not None:return False
    if not (user.is_superuser or user.has_perm('core.change_dispute')):return False
    grants=InvestigationGrant.objects.filter(operator=user,contract_id=asset.contract_id,case_type='dispute',expires_at__gt=timezone.now())
    cases=Dispute.objects.filter(pk__in=grants.values('case_id'),contract_id=asset.contract_id,target_type='milestone',status='open')
    for case in cases:
        milestone=Milestone.objects.filter(pk=case.target_id,contract_id=asset.contract_id).first()
        attachment_ids=(milestone.submission or {}).get('attachment_ids',[]) if milestone else []
        if str(asset.pk) in {str(value) for value in attachment_ids}:return True
    return False

def file_response(request,id,screenshot=False):
    # Lock covers authorization and opening the file. No independent public URL exists.
    with transaction.atomic():
        a=object_get(Asset,id,True);require(a.purged_at is None,'file_expired','Dosya saklama süresi doldu.',410)
        if screenshot:
            own=a.owner_id==request.user.pk
            if isinstance(request.auth,DeviceCredential):require(own,'device_owner','Cihaz yalnız kendi görüntüsüne erişebilir.')
            related=bool(a.contract_id and a.contract.employer_id==request.user.pk and a.state=='released' and not PrivacyRequest.objects.filter(asset=a,status='pending').exists())
            require(own or related or pending_case(request.user,a),'image_scope','Görüntü erişimi kapalı.',404)
        else:
            require(a.captured_at is None,'asset_scope','Takip görüntüsü ayrı erişim kontrolü kullanır.',404)
            if a.owner_id!=request.user.pk:
                if pending_milestone_attachment(request.user,a):pass
                elif a.conversation_id:conversation_access(request.user,a.conversation)
                elif a.contract_id:contract_access(request.user,a.contract)
                elif a.job_id:require(job_asset_access(request.user,a.job),'job_attachment_scope','İlan dosyası özel.',404)
                else:raise Problem('file_scope','Dosya yetkisi yok.',404)
        path=settings.PRIVATE_ROOT/a.storage_key;require(path.is_file(),'file_missing','Dosya bulunamadı.',404)
        response=FileResponse(path.open('rb'),as_attachment=not screenshot,filename=a.filename,content_type=a.mime);response['Cache-Control']='private, no-store';response['X-Content-Type-Options']='nosniff';return response

@transaction.atomic
def screenshot_action(request,id,action):
    a=object_get(Asset,id,True);require(a.owner_id==request.user.pk and a.captured_at is not None and a.purged_at is None,'image_owner','Kendi görüntünüz gerekir.',404)
    prior=PrivacyRequest.objects.filter(asset=a).first()
    if action=='privacy':
        if prior:return dto(prior)
        require(a.state=='preview','image_published','Görüntü zaten yayımlandı; yayın öncesi talep gerekir.',409);fields(request.data,['reason']);a.state='held';a.publish_at=None;a.publication_ready_at=None;a.save();return dto(PrivacyRequest.objects.create(asset=a,reason=request.data['reason']))
    require(not prior or prior.status!='pending','privacy_pending','Görüntü moderasyon sonucu bekliyor.',409)
    require(a.state=='preview','image_state','Görüntü önizleme durumunda değil.',409)
    if action=='publish':a.state='released';a.publish_at=None
    elif action=='review-ready':
        a.publication_ready_at=timezone.now();seconds=policy().get('preview_seconds');a.publish_at=a.publication_ready_at+timedelta(seconds=int(seconds)) if seconds is not None else None
    else:raise Problem('not_found','Görüntü işlemi bulunamadı.',404)
    a.save();return {'id':a.pk,'state':a.state,'publication_ready_at':a.publication_ready_at,'review_due_at':a.publish_at}

@transaction.atomic
def privacy_resolve(request,id):
    row=object_get(PrivacyRequest,id,True);a=object_get(Asset,row.asset_id,True);investigation(request.user,a.contract,row.pk,'privacy');require(row.status=='pending','case_closed','Talep sonuçlandırıldı.',409);fields(request.data,['decision','reason']);choice=request.data['decision'];require(choice in ['withhold','publish'],'decision_invalid','Geçerli moderasyon kararı gerekir.',400)
    a.state='withheld' if choice=='withhold' else 'released';a.publish_at=None;a.save();row.status='resolved';row.decision=choice;row.resolved_at=timezone.now();row.save();audit(request.user,row,request.data['reason'],choice);notify(a.owner,'privacy.resolved','Görüntü talebi sonuçlandırıldı; süre/ücret değişmedi.',row);return dto(row)

def funding_state(contract):
    now=timezone.now()
    if contract.status!='active':return None,'contract_inactive'
    if contract.work_type=='fixed':
        targets=contract.milestones.filter(status__in=['funded','in_progress']);target=next((m for m in targets if Payment.objects.filter(target_type='milestone',target_id=m.pk,status='funded',mode=settings.PAYMENT_PROVIDER).exists()),None);return target,None if target else 'milestone_unfunded'
    target=contract.weeks.filter(starts_at__lte=now,ends_at__gt=now,status='funded').first();valid=target and Payment.objects.filter(target_type='week',target_id=target.pk,status='funded',mode=settings.PAYMENT_PROVIDER).exists();return target,None if valid else 'week_unfunded'

def remaining(contract,week):
    week_totals(week)
    outstanding=sum(s.reserved_seconds-s.used_seconds for s in WorkSession.objects.filter(contract=contract,created_at__gte=week.starts_at,created_at__lt=week.ends_at,stopped_at=None))
    return max(0,int(week.limit_hours*3600)-week.worked_seconds-outstanding)

@transaction.atomic
def tracker_contracts(request):
    rows=Contract.objects.filter(workers__user=request.user,workers__active=True).distinct().order_by('-created_at')
    def transform(c):
        target,blocked=funding_state(c)
        if isinstance(target,Week) and str(request.user.pk) not in target.rate_snapshot:blocked='rate_not_in_period'
        state=dto(c);state.update(tracker_ready=blocked is None and policy().get('idle_seconds') is not None,blocked_reason=blocked or ('idle_unconfigured' if policy().get('idle_seconds') is None else None),remaining_seconds=remaining(c,target) if isinstance(target,Week) else None,funded_until=target.ends_at if isinstance(target,Week) else None);return state
    return page(request,rows,transform)

@transaction.atomic
def session_start(request):
    data=request.data;fields(data,['contract','client_id','monitor_id','capabilities']);User.objects.select_for_update(no_key=True).get(pk=request.user.pk);c=object_get(Contract,data['contract'],True);worker(request.user,c);setting_value('idle_seconds')
    caps=data['capabilities'];require(isinstance(caps,dict) and all(caps.get(k) is True for k in ['screen_capture','input_counting','active_app']),'tracker_capability','Takip izinleri eksik.',409)
    require(not WorkSession.objects.filter(owner=request.user,stopped_at=None).exists(),'open_session','Önceki çalışma yetkisini senkronize edip kapatın.',409)
    target,blocked=funding_state(c);require(blocked is None,'unfunded','Yeni ücretli çalışma için fon yok.',409)
    count=int(data.get('requested_seconds',600));require(1<=count<=600,'grant_size','Tek aktif bölüm 1–600 saniye olabilir.',400)
    if isinstance(target,Week):
        target=object_get(Week,target.pk,True);require(str(request.user.pk) in target.rate_snapshot,'rate_not_in_period','Çalışanın kabul edilmiş ücreti bu ön fonlanan dönem snapshotında yok; yeni dönemi bekleyin.',409);count=min(count,remaining(c,target));require(count>0,'weekly_limit','Ortak haftalık sınır doldu.',409);end=min(target.ends_at,timezone.now()+timedelta(seconds=count))
        funding={'week':str(target.pk),'milestone':None,'reserved_amount':str((Decimal(count)*Decimal(target.rate_snapshot[str(request.user.pk)])/3600).quantize(CENT)),'currency':'TRY'}
    else:end=timezone.now()+timedelta(seconds=count);funding={'week':None,'milestone':str(target.pk),'reserved_amount':str(target.amount),'currency':'TRY'}
    row=WorkSession.objects.create(owner=request.user,contract=c,client_id=identity(data['client_id']),memo=str(data.get('memo','')),ends_at=end,reserved_seconds=count,monitor_id=str(data['monitor_id']),funding=funding);return dto(row)


def block_digest(data,upload):
    values={k:str(data.get(k,'')) for k in ['client_id','session','starts_at','ends_at','seconds','key_count','mouse_count','active_app','captured_at','privacy_intent','privacy_reason']}
    if upload:values['screenshot_hash']=hashlib.sha256(upload.read()).hexdigest();upload.seek(0)
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()

@transaction.atomic
def ingest(request):
    data=request.data;fields(data,['client_id','session','starts_at','ends_at','seconds']);upload=request.FILES.get('screenshot');signature=block_digest(data,upload);client=identity(data['client_id'])
    User.objects.select_for_update(no_key=True).get(pk=request.user.pk)
    existing=TimeBlock.objects.filter(owner=request.user,client_id=client).first()
    if existing:require(existing.digest==signature,'client_conflict','Aynı kayıt kimliği farklı içerikle gönderildi.',409);return dto(existing)
    s=object_get(WorkSession,data['session'],True);require(s.owner_id==request.user.pk);require(s.stopped_at is None,'session_stopped','Kapatılmış yetkiye yeni bölüm eklenemez.',409);c=object_get(Contract,s.contract_id,True);worker(request.user,c)
    start,end=instant(data['starts_at']),instant(data['ends_at']);seconds=int(data['seconds']);span=(end-start).total_seconds()
    require(0<seconds<=span<=600 and start>=s.created_at-timedelta(seconds=2) and end<=s.ends_at and end<=timezone.now()+timedelta(seconds=2),'block_interval','Kayıt yetkilendirilmiş zaman aralığında olmalıdır.',409)
    require(s.used_seconds+seconds<=s.reserved_seconds,'grant_limit','Çalışma yetkisi sınırı aşıldı.',409);overlap(request.user,start,end)
    if s.funding.get('week'):
        week=object_get(Week,s.funding['week'],True);require(week.status=='funded','period_closed','Dönem kapandı; offline kayıt destek incelemesi gerektiriyor.',409)
    else:
        milestone=object_get(Milestone,s.funding['milestone'],True);require(milestone.status in ['funded','in_progress'],'milestone_closed','Aşama çalışmaya kapalı.',409)
    active=str(data.get('active_app',''));require(len(active)<=160 and not re.search(r'[\\/\n\r]',active),'active_app_invalid','Yalnız uygulama adı; dosya yolu/başlık alınmaz.',400)
    for key in ['key_count','mouse_count']:require(0<=int(data.get(key,0))<=2147483647,'activity_invalid','Geçerli etkinlik sayacı gerekir.',400)
    intent=str(data.get('privacy_intent','false')).lower() in ['true','1'];require(not intent or (upload and data.get('privacy_reason')),'privacy_fields','Kişisel bilgi talebi için görüntü ve gerekçe gerekir.',400)
    captured=instant(data['captured_at']) if upload else None
    if captured:require(start<=captured<=end,'capture_interval','Görüntü kayıt aralığında alınmalıdır.',400)
    a=save_asset(request.user,upload,contract=c,screenshot=True,captured_at=captured) if upload else None
    if a and intent:a.state='held';a.save();PrivacyRequest.objects.create(asset=a,reason=data['privacy_reason'])
    row=TimeBlock.objects.create(owner=request.user,session=s,client_id=client,starts_at=start,ends_at=end,seconds=seconds,key_count=int(data.get('key_count',0)),mouse_count=int(data.get('mouse_count',0)),active_app=active,screenshot=a,digest=signature)
    s.used_seconds+=seconds;s.save(update_fields=['used_seconds']);return dto(row)

@transaction.atomic
def session_stop(request,id):
    s=object_get(WorkSession,id,True);require(s.owner_id==request.user.pk)
    if s.stopped_at:return dto(s)
    supplied=request.data.get('final_client_ids',[]);require(isinstance(supplied,list),'final_ids','Senkronize bölüm kimlikleri gerekir.',400)
    actual={str(x) for x in TimeBlock.objects.filter(session=s).values_list('client_id',flat=True)};require(set(map(str,supplied))==actual,'pending_uploads','Bütün bölümler sunucu ACK almalıdır.',409)
    s.stopped_at=timezone.now();s.save();return dto(s)

def worklog(request,id):
    c=object_get(Contract,id)
    if request.user.is_staff and not member_contracts(request.user).filter(pk=c.pk).exists():
        require(pending_staff_dispute(request.user,c),'investigation_scope','Açık itiraz inceleme yetkisi gerekir.');investigation(request.user,c)
    else:contract_access(request.user,c)
    blocks=TimeBlock.objects.filter(session__contract=c).select_related('owner','session','screenshot').order_by('starts_at');manual=ManualTime.objects.filter(contract=c).order_by('starts_at')
    if request.user.pk!=c.employer_id and not pending_staff_dispute(request.user,c):blocks=blocks.filter(owner=request.user);manual=manual.filter(owner=request.user)
    weeks=c.weeks.all();milestones=c.milestones.all()
    if pending_staff_dispute(request.user,c) and request.user.pk!=c.employer_id:
        grants=InvestigationGrant.objects.filter(operator=request.user,contract=c,case_type='dispute',expires_at__gt=timezone.now())
        cases=Dispute.objects.filter(pk__in=grants.values('case_id'),status='open');query=Q(pk__in=[]);manual_query=Q(pk__in=[])
        for case in cases:
            query|=Q(**{'session__funding__'+case.target_type:str(case.target_id)})
            if case.target_type=='week':
                period=Week.objects.get(pk=case.target_id);manual_query|=Q(starts_at__gte=period.starts_at,ends_at__lte=period.ends_at)
        blocks=blocks.filter(query);manual=manual.filter(manual_query);weeks=weeks.filter(pk__in=cases.filter(target_type='week').values('target_id'));milestones=milestones.filter(pk__in=cases.filter(target_type='milestone').values('target_id'))
    seconds=sum(b.seconds for b in blocks)+sum(int((m.ends_at-m.starts_at).total_seconds()) for m in manual.filter(status='approved'))
    weeks=list(weeks);milestones=list(milestones)
    if c.work_type=='fixed':gross=sum((m.amount for m in milestones),Decimal('0'));net=(gross*Decimal('0.90')).quantize(CENT);basis='fixed_target_amount'
    else:gross=sum((w.gross for w in weeks),Decimal('0'));net=sum((w.net for w in weeks),Decimal('0'));basis='hourly_worked_amount'
    return {'blocks':[dto(b) for b in blocks],'manual_time':[dto(m) for m in manual],'weeks':[dto(w) for w in weeks],'milestones':[dto(m) for m in milestones],'summary':{'seconds':seconds,'gross':gross,'net':net,'currency':'TRY','basis':basis}}

def pending_staff_dispute(user,contract):
    if not user.is_staff or not (user.is_superuser or user.has_perm('core.change_dispute')):return False
    return InvestigationGrant.objects.filter(operator=user,contract=contract,case_type='dispute',case_id__in=Dispute.objects.filter(contract=contract,status='open').values('pk'),expires_at__gt=timezone.now()).exists()
