import secrets
import os
import json
import hmac
import hashlib
import uuid
import re
from datetime import date, timedelta
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from .common import *
from .providers import Iyzico, phone_send
from .security import digest, rate_limit
from .serialization import dto,user_dto,profile

PUBLIC = {'config','auth/csrf','auth/register','auth/login','auth/device-login','auth/password-reset','auth/password-reset-confirm','verification/student-confirm'}
POLICY_KEYS = {'post_cost','apply_cost','boost_cost','boost_hours','initial_student','initial_employer','monthly_student','monthly_employer','credit_price','withdraw_minimum','idle_seconds','preview_seconds','withdraw_schedule','payment_retention_days','contract_retention_days','capabilities'}

def readiness():
    values=policy(); missing=[]
    keys=['post_cost','apply_cost','boost_cost','boost_hours','initial_student','initial_employer','monthly_student','monthly_employer','credit_price','withdraw_minimum','idle_seconds','preview_seconds','withdraw_schedule']
    missing += ['policy:'+k for k in keys if values.get(k) is None]
    missing += [name for name in ['STEP_FIELD_ENCRYPTION_KEY','STEP_API_URL','STEP_SMTP_HOST','STEP_SMTP_FROM','STEP_WEB_URL','STEP_IYZICO_API_KEY','STEP_IYZICO_SECRET_KEY','STEP_NETGSM_USER','STEP_NETGSM_PASSWORD','STEP_NETGSM_HEADER'] if not __import__('os').environ.get(name)]
    capabilities=values.get('capabilities',{})
    missing += ['capability:'+k for k in ['merchant_kyc','underwriting','partial_release','unused_refund','rollover','withdrawal','bank_reconciliation','os_packages'] if capabilities.get(k) is not True]
    if not University.objects.exists(): missing.append('university_domains')
    if settings.PAYMENT_PROVIDER!='simulator':missing.append('provider:on_demand_bank_result_unavailable')
    if settings.STEP_MODE=='live' and settings.PAYMENT_PROVIDER!='iyzico_live': missing.append('live_provider')
    return missing

def config(request):
    values=policy()
    return {'mode':settings.STEP_MODE,'payment_provider':settings.PAYMENT_PROVIDER,'payment_ready':(settings.DEBUG and settings.STEP_MODE=='test' and settings.PAYMENT_PROVIDER=='simulator') or not readiness(),'payment_requires_buyer':settings.PAYMENT_PROVIDER!='simulator','payout_ready':policy().get('withdraw_minimum') is not None and policy().get('withdraw_schedule') is not None and (settings.STEP_MODE=='test' and settings.DEBUG and settings.PAYMENT_PROVIDER=='simulator'),'verification_required':settings.STEP_MODE=='live','credit_policy':{k:values.get(k) for k in ['post_cost','apply_cost','boost_cost','boost_hours','initial_student','initial_employer','monthly_student','monthly_employer','credit_price','withdraw_minimum']},'tracker_policy':{k:values.get(k) for k in ['idle_seconds','preview_seconds']},'categories':[dto(c) for c in Category.objects.all().order_by('name')],'production_readiness_missing':readiness() if request.user.is_authenticated and request.user.is_staff else []}

def password(value,user=None):
    try: validate_password(value,user)
    except ValidationError as exc: raise Problem('password_invalid',' '.join(exc.messages))

def auth(request, action):
    data=request.data
    if action=='csrf': return {'csrf_token':get_token(request._request)}
    if action=='me': return user_dto(request.user)
    if action=='logout':
        if isinstance(request.auth,DeviceCredential):
            request.auth.revoked_at=timezone.now();request.auth.save(update_fields=['revoked_at'])
        else: logout(request._request)
        return None
    rate_limit(request,'auth.'+action)
    if action=='register':
        fields(data,['email','password','display_name','roles']); roles=data['roles']
        require(isinstance(roles,list) and roles and set(roles)<={'student','employer'},'invalid_roles','Geçerli roller gerekir.',400)
        from django.core.validators import validate_email
        try: validate_email(data['email'])
        except ValidationError: raise Problem('email_invalid','Geçerli e-posta gerekir.')
        password(data['password'])
        require(not User.objects.filter(email=data['email'].casefold()).exists(),'email_registered','Bu e-posta kullanılıyor.',409)
        with transaction.atomic():
            u=User.objects.create_user(email=data['email'],password=data['password'],display_name=str(data['display_name'])[:120],roles=roles)
            initial_grants(u)
        login(request._request,u);return user_dto(u)
    if action in {'login','device-login'}:
        fields(data,['email','password']);u=authenticate(request._request,email=data['email'].casefold(),password=data['password'])
        require(u is not None,'invalid_credentials','E-posta veya şifre hatalı.',401)
        if action=='login':login(request._request,u);return user_dto(u)
        raw=secrets.token_urlsafe(48); expires=timezone.now()+timedelta(seconds=settings.DEVICE_TOKEN_SECONDS)
        DeviceCredential.objects.create(user=u,name=str(data.get('device_name','Tracker'))[:100],digest=digest(raw),expires_at=expires,password_digest=digest(u.password))
        return {'token':raw,'expires_at':expires,'user':user_dto(u)}
    if action=='password-reset':
        fields(data,['email']);require(bool(settings.EMAIL_HOST and settings.DEFAULT_FROM_EMAIL and settings.WEB_URL),'email_unconfigured','E-posta hizmeti yapılandırılmadı.',503)
        encrypted_text('reset-key-preflight')
        u=User.objects.filter(email=data['email'].casefold(),is_active=True).first()
        if u:
            raw=secrets.token_urlsafe(40)
            with transaction.atomic():
                c=Challenge.objects.create(user=u,purpose='reset',digest=digest(raw),expires_at=timezone.now()+timedelta(hours=1))
                Outbox.objects.create(event_key='reset:'+str(c.pk),recipient=u,subject='STEP şifre sıfırlama',body=encrypted_text(settings.WEB_URL.rstrip('/')+'/reset-password?token='+raw))
        return {'detail':'Hesap varsa şifre sıfırlama bağlantısı gönderilecektir.'}
    if action=='password-reset-confirm':
        fields(data,['token','password']);password(data['password'])
        with transaction.atomic():
            c=Challenge.objects.select_for_update().filter(purpose='reset',digest=digest(data['token']),used_at=None,expires_at__gt=timezone.now()).first()
            require(c is not None,'reset_invalid','Bağlantı geçersiz veya süresi doldu.',400)
            u=User.objects.select_for_update(no_key=True).get(pk=c.user_id);password(data['password'],u);u.set_password(data['password']);u.save(update_fields=['password']);c.used_at=timezone.now();c.save();DeviceCredential.objects.filter(user=u,revoked_at=None).update(revoked_at=timezone.now())
        return None
    raise Problem('not_found','Auth yolu bulunamadı.',404)

def initial_grants(user, monthly=False):
    values=policy(); wallet=wallet_for(user)
    prefix='monthly' if monthly else 'initial'
    period=timezone.localdate().strftime('%Y-%m') if monthly else 'once'
    for role in user.roles:
        count=values.get(prefix+'_'+role)
        if count is not None:
            credit_change(wallet,int(count),prefix,f'{settings.STEP_MODE}:{prefix}:{user.pk}:{role}:{period}')

def profile_endpoint(request, id=None):
    if id:
        u=object_get(User,id);require('student' in u.roles,'not_found','Profil bulunamadı.',404);return profile(u)
    if request.method=='PATCH':
        data=request.data; allowed=['university','department','bio','skills','hourly_rate','photo','portfolio_links']
        result={**request.user.profile,**{k:data[k] for k in allowed if k in data}}
        if 'student' in request.user.roles:fields(result,['university','department','bio','skills','hourly_rate'])
        if result.get('hourly_rate') is not None:result['hourly_rate']=str(money(result['hourly_rate']))
        require(isinstance(result.get('skills',[]),list),'skills_invalid','Beceri listesi gerekir.',400)
        links=result.get('portfolio_links',[]);require(isinstance(links,list),'links_invalid','Portföy listesi gerekir.',400)
        for link in links:fields(link,['title','url','kind']);safe_url(link['url'])
        if result.get('photo'):safe_url(result['photo'])
        request.user.profile=json_safe(result);request.user.save(update_fields=['profile'])
    return profile(request.user)

def verification(request,action):
    data=request.data
    if action=='student-confirm':
        fields(data,['token'])
        with transaction.atomic():
            c=Challenge.objects.select_for_update().filter(digest=digest(data['token']),purpose='student',used_at=None,expires_at__gt=timezone.now()).first()
            require(c is not None,'challenge_invalid','Doğrulama bağlantısı geçersiz.',400)
            e,_=Eligibility.objects.get_or_create(user=c.user);now=timezone.now()
            e.student_email=c.target;e.birth_date=date.fromisoformat(c.data['birth_date']);e.education_level=c.data['education_level'];e.status='verified'
            try:e.verified_until=now.replace(year=now.year+1)
            except ValueError:e.verified_until=now.replace(year=now.year+1,day=28)
            e.save();c.used_at=now;c.save()
            return {'verified_until':e.verified_until}
    u=request.user
    if action=='student':
        student(u);fields(data,['student_email','birth_date','education_level'])
        email=str(data['student_email']).casefold();domain=email.rsplit('@',1)[-1]
        require(any(domain in university.domains for university in University.objects.all()),'university_domain','Öğrenci e-posta alan adı listede değil.',400)
        require(data['education_level'] in ['associate','bachelor','master','doctorate'],'program_invalid','Geçerli üniversite programı gerekir.',400)
        try:birth=date.fromisoformat(data['birth_date'])
        except ValueError:raise Problem('birth_invalid','Geçerli doğum tarihi gerekir.')
        today=timezone.localdate();require(today.year-birth.year-((today.month,today.day)<(birth.month,birth.day))>=18,'age_requirement','18 yaş koşulu gerekir.',400)
        require(settings.EMAIL_HOST and settings.DEFAULT_FROM_EMAIL and settings.WEB_URL,'email_unconfigured','E-posta hizmeti eksik.',503)
        raw=secrets.token_urlsafe(40)
        with transaction.atomic():
            c=Challenge.objects.create(user=u,purpose='student',target=email,digest=digest(raw),data={'birth_date':birth.isoformat(),'education_level':data['education_level']},expires_at=timezone.now()+timedelta(days=1))
            # University destination is the challenge target, never the account contact email.
            Outbox.objects.create(event_key='student:'+str(c.pk),recipient=u,subject='STEP üniversite e-posta doğrulaması',body=encrypted_text(settings.WEB_URL.rstrip('/')+'/verify-student?token='+raw),destination=email)
        return {'detail':'Üniversite e-postasına doğrulama gönderimi sıraya alındı.'}
    if action=='student-status':
        require(data.get('status') in ['graduated','access_lost'],'status_invalid','Geçerli durum gerekir.',400)
        e,_=Eligibility.objects.get_or_create(user=u);e.status=data['status'];e.save();return user_dto(u)['verification']
    if action=='phone/start':
        fields(data,['phone']);rate_limit(request,'phone');code=f'{secrets.randbelow(1000000):06d}'
        c=Challenge.objects.create(user=u,purpose='phone',id=(challenge_id:=uuid.uuid4()),target=re.sub(r'[^0-9+]','',str(data['phone'])),digest=hmac.new(settings.SECRET_KEY.encode(),(str(challenge_id)+':'+code).encode(),hashlib.sha256).hexdigest(),expires_at=timezone.now()+timedelta(minutes=5))
        try:phone_send(c.target,code)
        except Problem:c.used_at=timezone.now();c.save();raise
        return {'detail':'Telefon kodu gönderildi.'}
    if action=='phone/confirm':
        fields(data,['code']);rate_limit(request,'phone-confirm')
        with transaction.atomic():
            c=Challenge.objects.select_for_update().filter(user=u,purpose='phone',used_at=None,expires_at__gt=timezone.now()).order_by('-created_at').first()
            require(c is not None and c.attempts<5,'otp_invalid','Kod geçersiz veya süresi doldu.',400)
            c.attempts+=1;c.save(update_fields=['attempts'])
            matched=secrets.compare_digest(c.digest,hmac.new(settings.SECRET_KEY.encode(),(str(c.pk)+':'+str(data['code'])).encode(),hashlib.sha256).hexdigest())
            if matched:
                c.used_at=timezone.now();c.save();v,_=EmployerVerification.objects.get_or_create(user=u);v.phone_verified_at=timezone.now();v.verified_phone=c.target;v.details={**v.details,'phone':c.target};v.save()
        require(matched,'otp_invalid','Kod hatalı.',400);return user_dto(u)['verification']
    if action=='employer':
        require('employer' in u.roles);fields(data,['kind','phone','legal_name']);require(data['kind'] in ['individual','company'],'kind_invalid','Geçerli işveren türü gerekir.',400)
        if data['kind']=='company':fields(data,['company_name','company_registration'])
        v,_=EmployerVerification.objects.get_or_create(user=u);v.kind=data['kind'];v.status='pending';new_phone=re.sub(r'[^0-9+]','',str(data['phone']));
        if new_phone!=v.verified_phone:v.phone_verified_at=None
        data={**data,'phone':new_phone};v.details={**v.details,**{k:data.get(k) for k in ['phone','legal_name','company_name','company_registration']}};v.save();return dto(v)
    raise Problem('not_found','Doğrulama yolu bulunamadı.',404)

def payment_profile(request):
    data=request.data;fields(data,['legal_name','iban']);binding=bank_digest(data['iban'])
    if settings.PAYMENT_PROVIDER=='simulator' and settings.DEBUG and settings.STEP_MODE=='test':
        u=request.user;u.bank_name=data['legal_name'];u.bank_digest=binding;u.iban_masked=str(data['iban'])[:4]+'…'+str(data['iban'])[-4:];u.save(update_fields=['bank_name','bank_digest','iban_masked']);return {'status':'simulated','iban_masked':u.iban_masked,'provider_verified':False}
    fields(data,['phone','identity_number','address'])
    require(settings.PAYMENT_PROVIDER!='simulator','provider_unavailable','Gerçek alıcı kaydı için sağlayıcı gerekir.',503)
    require(os.environ.get('STEP_IYZICO_API_KEY') and os.environ.get('STEP_IYZICO_SECRET_KEY'),'provider_unconfigured','Sağlayıcı anahtarları eksik.',503)
    name=str(data['legal_name']);parts=name.rsplit(' ',1);encrypted=encrypted_text(json.dumps(dict(data),ensure_ascii=False))
    with transaction.atomic():
        u=User.objects.select_for_update(no_key=True).get(pk=request.user.pk)
        if u.submerchant_key:
            require(u.bank_digest==binding and u.bank_name.casefold()==name.casefold(),'bank_profile_locked','Kayıtlı banka değişikliği sağlayıcı/yönetim incelemesi gerektirir.',409);return {'status':'onboarded','iban_masked':u.iban_masked}
        op,created=ProviderOperation.objects.get_or_create(event_key='onboarding:'+str(u.pk),defaults={'kind':'onboarding','state':'processing','payload':{'user':str(u.pk),'encrypted_request':encrypted},'lease_until':timezone.now()+timedelta(minutes=2)})
        if not created and op.state!='failed':return {'status':'pending','provider_verified':False,'detail':'Önceki dış alıcı kaydı uzlaştırma bekliyor; tekrar gönderilmedi.'}
        if not created:
            op.state='processing';op.payload={'user':str(u.pk),'encrypted_request':encrypted};op.lease_until=timezone.now()+timedelta(minutes=2);op.save()
    try:
        result=Iyzico().onboard({'locale':'tr','conversationId':str(op.pk),'subMerchantExternalId':str(request.user.pk),'subMerchantType':'PERSONAL','address':data['address'],'gsmNumber':data['phone'],'email':request.user.email,'contactName':parts[0],'contactSurname':parts[-1],'name':name,'iban':data['iban'],'identityNumber':data['identity_number'],'currency':'TRY'})
        require(bool(result.get('subMerchantKey')),'provider_unknown','Alt üye anahtarı doğrulanmadı.',502)
    except Problem as exc:
        ProviderOperation.objects.filter(pk=op.pk).update(state='failed' if exc.detail['code']=='provider_rejected' else 'unknown',result={'error_code':exc.detail['code']},lease_until=None)
        raise
    with transaction.atomic():
        u=User.objects.select_for_update(no_key=True).get(pk=request.user.pk);u.submerchant_key=result['subMerchantKey'];u.bank_name=name;u.bank_digest=binding;u.iban_masked=str(data['iban'])[:4]+'…'+str(data['iban'])[-4:];u.save(update_fields=['submerchant_key','bank_name','bank_digest','iban_masked']);ProviderOperation.objects.filter(pk=op.pk).update(state='confirmed',result={'provider_verified':True},lease_until=None)
    return {'status':'onboarded','iban_masked':u.iban_masked}

def reconcile_onboarding(request,op):
    result=Iyzico().submerchant_retrieve(op.payload['user']);data=json.loads(decrypted_text(op.payload['encrypted_request']))
    require(str(result.get('subMerchantExternalId'))==op.payload['user'] and result.get('subMerchantKey') and result.get('currency')=='TRY' and bank_digest(result.get('iban',''))==bank_digest(data['iban']) and str(result.get('name','')).casefold()==str(data['legal_name']).casefold(),'onboarding_binding','Sağlayıcı alıcı/banka kanıtı eşleşmiyor.',409)
    with transaction.atomic():
        current=object_get(ProviderOperation,op.pk,True);u=User.objects.select_for_update(no_key=True).get(pk=op.payload['user']);u.submerchant_key=result['subMerchantKey'];u.bank_name=data['legal_name'];u.bank_digest=bank_digest(data['iban']);u.iban_masked=str(data['iban'])[:4]+'…'+str(data['iban'])[-4:];u.save(update_fields=['submerchant_key','bank_name','bank_digest','iban_masked']);current.state='confirmed';current.result={'provider_verified':True};current.save();audit(request.user,current,request.data['reason'],'onboarding.reconcile')
    from .payments import operation_dto
    return operation_dto(current)
