import hashlib
import json
import re
import uuid
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponseBase
from django.utils import timezone
from rest_framework.authentication import CSRFCheck
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from . import accounts,market,contracts,payments,tracking,operations
from .common import *
from .security import Problem,digest,require
from .serialization import dto,profile


def user_profiles(request,id=None):
    if id:return accounts.profile_endpoint(request,id)
    rows=User.objects.filter(roles__contains=['student'],is_active=True).order_by('display_name')
    if request.query_params.get('q'):rows=rows.filter(display_name__icontains=request.query_params['q'])
    if request.query_params.get('skill'):rows=rows.filter(profile__skills__contains=[request.query_params['skill']])
    return page(request,rows,profile)

def public_teams(request,id=None):
    def public(row):return {'id':row.pk,'name':row.name,'description':row.description,'leader_name':row.leader.display_name}
    if id:return public(object_get(Team,id))
    return page(request,Team.objects.select_related('leader').order_by('name'),public)

def preferences(request):
    require(set(request.data)<= {'in_app','email'} and all(isinstance(x,bool) for x in request.data.values()),'preferences_invalid','Bildirim tercihleri boolean olmalıdır.',400);request.user.preferences={**request.user.preferences,**dict(request.data)};request.user.save(update_fields=['preferences']);return request.user.preferences

def notifications(request,id=None):
    if id:
        row=object_get(Notification,id);require(row.recipient_id==request.user.pk);row.read_at=timezone.now();row.save();return dto(row)
    return page(request,Notification.objects.filter(recipient=request.user).order_by('-created_at'),dto)

def wallet(request):
    t=object_get(Team,request.query_params['team']) if request.query_params.get('team') else None;return dto(wallet_for(request.user,t))

def report(request,id):
    fields(request.data,['reason']);return dto(Report.objects.create(reporter=request.user,job=object_get(Job,id),reason=request.data['reason']))

def changes_list(request,leader=False):
    if leader:
        rows=LeaderChange.objects.filter(Q(team__leader=request.user)|Q(new_leader=request.user)|Q(contracts__employer=request.user))
        if request.user.is_staff:rows=LeaderChange.objects.all()
    else:rows=ContractChange.objects.filter(contract__in=member_contracts(request.user))
    return page(request,rows.distinct().order_by('-created_at'),dto)

def purchases(request):
    if request.method=='POST':return payments.credit_purchase(request)
    return page(request,CreditPurchase.objects.filter(Q(owner=request.user)|Q(wallet__team__leader=request.user)).order_by('-created_at'),dto)

def payment_list(request):
    return page(request,Payment.objects.filter(Q(owner=request.user)|Q(target_id__in=Milestone.objects.filter(contract__payee=request.user).values('pk'))|Q(target_id__in=Week.objects.filter(contract__payee=request.user).values('pk'))).distinct().order_by('-created_at'),dto)

def webhook(request):
    # Token alone is not settlement evidence; bind stored token then server retrieve.
    token=request.data.get('token');require(isinstance(token,str) and bool(token),'callback_invalid','Callback tokenı gerekir.',400)
    p=Payment.objects.filter(provider_token_digest=digest(token),mode=settings.PAYMENT_PROVIDER).first()
    if p is None:
        old=PaymentAttempt.objects.filter(provider_token_digest=digest(token),payment__mode=settings.PAYMENT_PROVIDER).first()
        if old:
            ProviderEvent.objects.get_or_create(digest=digest(settings.PAYMENT_PROVIDER+':'+token),defaults={'reference':str(old.conversation_id),'mode':old.payment.mode,'payment':old.payment});return {'detail':'Önceki terminal başarısız deneme kaydedildi; mevcut deneme değiştirilmedi.'}
    require(p is not None,'callback_unknown','Callback hedefi yok.',404)
    ProviderEvent.objects.get_or_create(digest=digest(settings.PAYMENT_PROVIDER+':'+token),defaults={'reference':str(p.pk),'mode':p.mode,'payment':p})
    original=request.user;request.user=p.owner
    try:return payments.reconcile(request,p.pk)
    finally:request.user=original

UUID=r'(?P<id>[0-9a-f-]{36})'
ROUTES=[
 ('config','GET',lambda r:accounts.config(r)),
 ('auth/(?P<action>csrf|register|login|logout|me|password-reset|password-reset-confirm|device-login)','GET,POST',lambda r,action:accounts.auth(r,action)),
 ('profile','GET,PATCH',lambda r:accounts.profile_endpoint(r)),
 ('profiles','GET',user_profiles),('profiles/'+UUID,'GET',user_profiles),
 ('team-invitations','GET',lambda r:page(r,Team.objects.filter(memberships__user=r.user,memberships__status='invited').order_by('-created_at'),lambda t:{'id':t.pk,'name':t.name,'description':t.description,'leader_name':t.leader.display_name,'membership_status':'invited'})),
 ('public-teams','GET',public_teams),('public-teams/'+UUID,'GET',public_teams),
 ('verification/(?P<action>student|student-confirm|student-status|phone/start|phone/confirm|employer)','POST',lambda r,action:accounts.verification(r,action)),
 ('payment-profile','POST',accounts.payment_profile),('preferences','PATCH',preferences),
 ('notifications','GET',notifications),('notifications/'+UUID+'/read','POST',notifications),
 ('jobs','GET,POST',lambda r:market.jobs(r)),('jobs/'+UUID,'GET,PATCH',lambda r,id:market.jobs(r,id)),
 ('jobs/'+UUID+'/(?P<action>publish|cancel)','POST',lambda r,id,action:market.jobs(r,id,action)),
 ('jobs/'+UUID+'/report','POST',report),('jobs/'+UUID+'/applications','GET,POST',lambda r,id:market.applications(r,job_id=id)),
 ('applications','GET',lambda r:market.applications(r)),('applications/'+UUID,'PATCH',lambda r,id:market.applications(r,id)),
 ('applications/'+UUID+'/(?P<action>withdraw|reject)','POST',lambda r,id,action:market.applications(r,id,action=action)),
 ('jobs/'+UUID+'/invitations','POST',lambda r,id:market.invitations(r,job_id=id)),('invitations','GET',lambda r:market.invitations(r)),('invitations/'+UUID+'/decline','POST',lambda r,id:market.invitations(r,id=id)),
 ('teams','GET,POST',lambda r:market.teams(r)),('teams/'+UUID,'GET,PATCH',lambda r,id:market.teams(r,id)),('teams/'+UUID+'/(?P<action>invite|membership|leader-change)','POST',lambda r,id,action:market.teams(r,id,action)),
 ('leader-changes','GET',lambda r:changes_list(r,True)),('leader-changes/'+UUID+'/approve','POST',market.leader_approve),
 ('contracts','GET,POST',lambda r:contracts.contracts(r)),('contracts/'+UUID,'GET',lambda r,id:contracts.contracts(r,id)),('contracts/'+UUID+'/(?P<action>accept|reoffer|changes|cancel|complete)','POST',lambda r,id,action:contracts.contracts(r,id,action)),
 ('contract-changes','GET',changes_list),('contract-changes/'+UUID+'/accept','POST',contracts.change_accept),
 ('milestones/'+UUID+'/(?P<action>start|submit|review)','POST',contracts.milestones),
 ('contracts/'+UUID+'/weeks','GET,POST',lambda r,id:contracts.weeks(r,contract_id=id)),('weeks/'+UUID+'/(?P<action>close|review)','POST',lambda r,id,action:contracts.weeks(r,id=id,action=action)),
 ('contracts/'+UUID+'/manual-time','GET,POST',lambda r,id:contracts.manual_time(r,contract_id=id)),('manual-time/'+UUID+'/review','POST',lambda r,id:contracts.manual_time(r,id=id)),
 ('disputes','GET,POST',lambda r:contracts.disputes(r)),('disputes/'+UUID+'/resolve','POST',lambda r,id:contracts.disputes(r,id)),('contracts/'+UUID+'/ratings','GET,POST',operations.ratings),
 ('credits','GET',wallet),('boosts','POST',market.boost),('credit-purchases','GET,POST',purchases),('credit-refunds','GET,POST',lambda r:operations.refund_requests(r)),('credit-refunds/'+UUID+'/resolve','POST',lambda r,id:operations.refund_requests(r,id)),
 ('money','GET',lambda r:payments.money_dto(r.user)),('payments','GET,POST',lambda r:payments.payment_start(r) if r.method=='POST' else payment_list(r)),('payments/'+UUID+'/retry','POST',payments.retry_payment),('payments/'+UUID+'/reconcile','POST',lambda r,id:payments.reconcile(r,id)),('payments/'+UUID+'/simulate','POST',lambda r,id:payments.reconcile(r,id,r.data.get('outcome'))),('payouts','GET,POST',payments.payouts),('payment-webhooks/iyzico','POST',webhook),
 ('conversations','GET',lambda r:operations.messaging(r)),('conversations/'+UUID,'GET',lambda r,id:operations.messaging(r,id)),('conversations/'+UUID+'/messages','GET,POST',lambda r,id:operations.messaging(r,id,'messages')),('attachments','POST',operations.attachments),('attachments/'+UUID+'/download','GET',lambda r,id:tracking.file_response(r,id)),
 ('tracker/config','GET',lambda r:{'idle_seconds':policy().get('idle_seconds'),'preview_seconds':policy().get('preview_seconds'),'supported':['windows','macos','linux-x11']}),('tracker/contracts','GET',tracking.tracker_contracts),('tracker/sessions','POST',tracking.session_start),('tracker/blocks','POST',tracking.ingest),('tracker/sessions/'+UUID+'/stop','POST',tracking.session_stop),
 ('contracts/'+UUID+'/worklog','GET',tracking.worklog),('screenshots/'+UUID+'/image','GET',lambda r,id:tracking.file_response(r,id,True)),('screenshots/'+UUID+'/(?P<action>publish|privacy|review-ready)','POST',tracking.screenshot_action),('privacy-requests/'+UUID+'/resolve','POST',tracking.privacy_resolve),
 ('admin/payments/'+UUID+'/reconcile','POST',payments.admin_reconcile_payment),('admin/provider-operations/'+UUID+'/reconcile','POST',payments.reconcile_operation),('admin/investigations/claim','POST',operations.claim),('admin/(?P<action>overview|universities|categories|policy|credit-grants|queue|audit)','GET,POST,PATCH',operations.admin_endpoint),('admin/(?P<action>universities|categories)/'+UUID,'PATCH',operations.admin_endpoint),('admin/(?P<action>reports|verifications)/'+UUID+'/resolve','POST',operations.admin_endpoint),('admin/payouts/'+UUID+'/process','POST',operations.process_payout),('admin/credit-refunds/'+UUID+'/resolve','POST',lambda r,id:operations.refund_requests(r,id)),('admin/users','GET',lambda r:admin_users(r)),
]

def signature(data):
    result={}
    for key in sorted(data):
        value=data[key]
        if isinstance(value,UploadedFile):
            result[key]={'file':hashlib.sha256(value.read()).hexdigest()};value.seek(0)
        else:result[key]=value
    return digest(json.dumps(result,sort_keys=True,cls=__import__('django.core.serializers.json',fromlist=['DjangoJSONEncoder']).DjangoJSONEncoder,separators=(',',':')))

class Endpoint(APIView):
    permission_classes=[AllowAny]
    def get(self,request,route):return self.run(request,route)
    def post(self,request,route):return self.run(request,route)
    def patch(self,request,route):return self.run(request,route)
    def run(self,request,route):
        environment_gate();route=route.strip('/');match=None;handler=None
        for pattern,methods,fn in ROUTES:
            found=re.fullmatch(pattern,route)
            if found:
                require(request.method in methods.split(','),'method_not_allowed','Bu yöntem desteklenmiyor.',405);match=found;handler=fn;break
        require(handler is not None,'not_found','API yolu bulunamadı.',404)
        public=route in accounts.PUBLIC or route=='payment-webhooks/iyzico' or (request.method=='GET' and (route=='jobs' or route.startswith('jobs/') and '/applications' not in route or route=='profiles' or route.startswith('profiles/') or route=='public-teams' or route.startswith('public-teams/')))
        require(public or request.user.is_authenticated,'authentication_required','Giriş yapmalısınız.',401)
        if route.startswith('auth/'):
            require(request.method==('GET' if route in ['auth/me','auth/csrf'] else 'POST'),'method_not_allowed','Auth yöntem uyumsuz.',405)
        if request.method not in ['GET','HEAD','OPTIONS'] and not isinstance(request.auth,DeviceCredential) and route not in ['auth/device-login','payment-webhooks/iyzico']:
            check=CSRFCheck(lambda req:None);check.process_request(request._request);reason=check.process_view(request._request,None,(),{});require(reason is None,'csrf_failed','CSRF doğrulaması başarısız.',403)
        database_only=not (route in ['payments','payment-profile','verification/phone/start','verification/phone/confirm','payment-webhooks/iyzico'] or re.fullmatch(r'payments/[0-9a-f-]+/(reconcile|retry)',route) or re.fullmatch(r'admin/(payments|provider-operations)/[0-9a-f-]+/reconcile',route) or re.fullmatch(r'admin/payouts/[0-9a-f-]+/process',route))
        mutable=request.method!='GET' and request.user.is_authenticated and not route.startswith('auth/') and route!='payment-webhooks/iyzico'
        if not mutable:return self.invoke(request,match,handler)
        key=request.headers.get('Idempotency-Key');require(key is not None,'idempotency_required','Idempotency-Key UUID gerekir.',400)
        key=identity(key);payload=signature(request.data);scope=settings.STEP_MODE+':'+str(request.user.pk)+':'+request.method+':'+digest(route)
        if database_only:
            with transaction.atomic():
                row,created=Idempotency.objects.get_or_create(scope=scope,key=key,defaults={'digest':payload})
                row=Idempotency.objects.select_for_update().get(pk=row.pk);require(row.digest==payload,'idempotency_conflict','Anahtar farklı istek içeriğiyle kullanıldı.',409)
                if row.response is not None:return Response(row.response,status=row.status)
                result=self.invoke(request,match,handler)
                row.response=json_safe(result.data) if result.data is not None else {};row.status=result.status_code;row.save()
                return result
        with transaction.atomic():
            row,created=Idempotency.objects.get_or_create(scope=scope,key=key,defaults={'digest':payload})
            row=Idempotency.objects.select_for_update().get(pk=row.pk);require(row.digest==payload,'idempotency_conflict','Anahtar farklı istek içeriğiyle kullanıldı.',409)
            if row.response is not None:return Response(row.response,status=row.status)
        if not created:
            # Recovery from committed resources, not a second external mutation.
            recovered=self.recover_external(request,route)
            if recovered is not None:return Response(json_safe(recovered))
            if '/reconcile' not in route:raise Problem('external_result_unknown','Dış işlem sonucu operatör uzlaştırması bekliyor; yeni işlem körlemesine gönderilmedi.',409)
        try:result=self.invoke(request,match,handler)
        except Problem:
            # Known failures remain retryable with the same key. Domain/provider pending records
            # stop a second remote effect when the previous result is ambiguous.
            Idempotency.objects.filter(pk=row.pk).delete()
            raise
        Idempotency.objects.filter(pk=row.pk).update(response=json_safe(result.data) if result.data is not None else {},status=result.status_code)
        return result
    def recover_external(self,request,route):
        if route=='payments':
            key=next((k for k in ['milestone','week','credit_purchase'] if request.data.get(k)),None)
            if key:
                row=Payment.objects.filter(owner=request.user,target_type=key,target_id=request.data[key],mode=settings.PAYMENT_PROVIDER).first()
                if row:return dto(row)
        if re.fullmatch(r'payments/[0-9a-f-]+/reconcile',route):
            row=object_get(Payment,route.split('/')[1]);require(row.owner_id==request.user.pk or (request.user.is_staff and (request.user.is_superuser or request.user.has_perm('core.change_payment'))))
            if row.status in ['funded','refunded','failed']:return dto(row)
        if re.fullmatch(r'payments/[0-9a-f-]+/retry',route):
            row=object_get(Payment,route.split('/')[1]);require(row.owner_id==request.user.pk)
            return dto(row)
        if re.fullmatch(r'admin/payouts/[0-9a-f-]+/process',route):
            require(request.user.is_staff and (request.user.is_superuser or request.user.has_perm('core.change_payout')));row=object_get(Payout,route.split('/')[2]);return dto(row)
        if re.fullmatch(r'admin/payments/[0-9a-f-]+/reconcile',route):
            return payments.admin_reconcile_payment(request,route.split('/')[2])
        if re.fullmatch(r'admin/provider-operations/[0-9a-f-]+/reconcile',route):
            return payments.reconcile_operation(request,route.split('/')[2])
        if route=='payment-profile' and request.user.submerchant_key:return {'status':'onboarded','iban_masked':request.user.iban_masked}
        if route=='verification/phone/start':return {'detail':'Telefon gönderimi yeniden yapılmadı; mevcut kod veya operatör sonucu kontrol edilmelidir.'}
        if route=='verification/phone/confirm':return self.invoke(request,re.fullmatch('verification/(?P<action>phone/confirm)',route),lambda r,action:accounts.verification(r,action)).data
        return None
    def invoke(self,request,match,handler):
        try:
            result=handler(request,**match.groupdict())
            if isinstance(result,HttpResponseBase):return result
            return Response(json_safe(result),status=204 if result is None else 200)
        except (ValueError,TypeError,KeyError,OverflowError) as exc:raise Problem('invalid_input','Alan türü veya zorunlu alan geçersiz.',400) from exc
        except IntegrityError as exc:raise Problem('record_conflict','Aynı kayıt veya çakışan durum zaten var.',409) from exc

def admin_users(request):
    require(request.user.is_staff and (request.user.is_superuser or request.user.has_perm('core.view_user')))
    rows=User.objects.all().order_by('display_name')
    if request.query_params.get('q'):rows=rows.filter(Q(display_name__icontains=request.query_params['q'])|Q(email__icontains=request.query_params['q']))
    return page(request,rows,lambda u:{'id':u.pk,'display_name':u.display_name,'email':u.email,'roles':u.roles})
