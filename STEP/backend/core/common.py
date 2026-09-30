import json
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlparse
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import *
from .security import Problem, require

CENT = Decimal('0.01')

def money(value):
    try:
        result = Decimal(str(value))
        require(result.is_finite() and result > 0 and result <= Decimal('99999999999999.99'), 'invalid_amount', 'Pozitif ve geçerli tutar gerekir.', 400)
        require(result == result.quantize(CENT), 'invalid_precision', 'Tutar iki ondalık basamak olmalıdır.', 400)
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise Problem('invalid_amount', 'Geçerli tutar gerekir.')

def decimal_hours(value):
    result = money(value)
    require(result<=Decimal('99999.99'),'hours_out_of_range','Saat değeri veri sınırını aşıyor.',400)
    return result

def instant(value):
    result = parse_datetime(str(value)) if value else None
    require(result is not None and timezone.is_aware(result), 'invalid_time', 'Saat dilimli ISO zaman gerekir.', 400)
    return result

def identity(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise Problem('invalid_id', 'UUID kimlik gerekir.')

def object_get(model, value, lock=False):
    qs = model.objects.select_for_update() if lock else model.objects
    row = qs.filter(pk=identity(value)).first()
    require(row is not None, 'not_found', 'Kayıt bulunamadı.', 404)
    return row

def fields(data, required):
    require(all(data.get(key) not in (None, '', []) for key in required), 'missing_fields', 'Zorunlu alanları tamamlayın.', 400)

def policy():
    row, _ = Policy.objects.get_or_create(pk=1)
    return row.values

def setting_value(key):
    value = policy().get(key)
    require(value is not None, 'policy_unconfigured', f'{key} yönetim tarafından yapılandırılmalıdır.', 409)
    return value

def student(user, apply=False):
    require('student' in user.roles, 'student_role', 'Öğrenci rolü gerekir.')
    if apply:
        fields(user.profile,['university','department','bio','skills','hourly_rate'])
        money(user.profile['hourly_rate'])
    if settings.STEP_MODE == 'live' and apply:
        eligible = Eligibility.objects.filter(user=user,status='verified',verified_until__gt=timezone.now()).first()
        require(eligible is not None, 'student_verification', 'Geçerli üniversite e-posta doğrulaması gerekir.', 409)
        today = timezone.localdate()
        birth = eligible.birth_date
        require(birth is not None and (today.year-birth.year-((today.month,today.day)<(birth.month,birth.day))) >= 18, 'age_requirement', '18 yaş koşulu sağlanmalıdır.', 409)

def employer(user):
    require('employer' in user.roles, 'employer_role', 'İşveren rolü gerekir.')
    if settings.STEP_MODE == 'live':
        require(EmployerVerification.objects.filter(user=user,status='verified',phone_verified_at__isnull=False).exists(), 'employer_verification', 'İşveren doğrulaması tamamlanmalıdır.', 409)

def contract_access(user, contract, party_only=False):
    is_party = user.pk in {contract.employer_id,contract.freelancer_id}
    if contract.team_id:
        is_party = is_party or contract.team.leader_id == user.pk
    require(is_party or (not party_only and contract.workers.filter(user=user,active=True).exists()), 'contract_scope', 'Sözleşmeye erişim yetkisi yok.', 404)

def representative(user, contract):
    require(contract.team.leader_id == user.pk if contract.team_id else contract.freelancer_id == user.pk)

def worker(user, contract):
    require(contract.workers.filter(user=user,active=True).exists(), 'worker_scope', 'Sözleşmede çalışan olarak listelenmelisiniz.')

def team_access(user, team, spend=False):
    require(team.leader_id == user.pk if spend else team.memberships.filter(user=user,status='active').exists())

def wallet_for(user, team=None, spend=False):
    if team:
        team_access(user, team, spend)
    kwargs = {'team':team} if team else {'user':user}
    row, _ = Wallet.objects.get_or_create(**kwargs, defaults={'mode':settings.STEP_MODE})
    require(row.mode == settings.STEP_MODE, 'mode_mismatch', 'Test kayıtları canlıda kullanılamaz.', 409)
    return row

def credit_change(wallet, delta, reason, event, source=None):
    existing = CreditEntry.objects.filter(event_key=event).first()
    if existing:
        return existing
    wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
    existing = CreditEntry.objects.filter(event_key=event).first()
    if existing:
        return existing
    require(wallet.balance + delta >= 0, 'insufficient_credits', 'Yeterli kredi yok.', 409)
    wallet.balance += delta
    wallet.save(update_fields=['balance'])
    return CreditEntry.objects.create(wallet=wallet,amount=delta,reason=reason,event_key=event,source=source,balance_after=wallet.balance)

def audit(user, row, reason, outcome):
    return AuditEvent.objects.create(actor=user,resource=row.__class__.__name__,resource_id=row.pk if isinstance(row.pk,uuid.UUID) else None,reason=reason,outcome=outcome)

def notify(user, kind, text, resource):
    event = f'{kind}:{resource.pk}:{user.pk}:{uuid.uuid4()}'
    if user.preferences.get('in_app', True):
        Notification.objects.create(recipient=user,kind=kind,text=text,resource_id=resource.pk)
    if user.preferences.get('email', True):
        Outbox.objects.create(event_key=event,recipient=user,subject='STEP '+kind,body=text)

def conversation_access(user, row):
    if row.contract_id:
        contract_access(user,row.contract)
    else:
        require(row.users.filter(pk=user.pk).exists(),'conversation_scope','Görüşmeye erişim yok.',404)

def member_contracts(user):
    return Contract.objects.filter(Q(employer=user)|Q(freelancer=user)|Q(team__leader=user)|Q(workers__user=user)).distinct()

def safe_url(value):
    parsed = urlparse(str(value))
    require(parsed.scheme in {'http','https'} and bool(parsed.hostname) and not parsed.username and not parsed.password, 'invalid_url', 'HTTP(S) bağlantı gerekir.', 400)
    return str(value)

def json_safe(value):
    return json.loads(json.dumps(value,cls=DjangoJSONEncoder))

def page(request, rows, transform):
    try:
        size = min(100,max(1,int(request.query_params.get('page_size',30))))
        number = max(1,int(request.query_params.get('page',1)))
    except ValueError:
        raise Problem('pagination','Sayfalama sayısal olmalıdır.')
    count = rows.count() if hasattr(rows,'filter') else len(rows)
    begin = (number-1)*size
    next_url = None
    if begin+size < count:
        query = request.query_params.copy()
        query['page'] = number+1
        next_url = request.path+'?'+query.urlencode()
    return {'results':[transform(row) for row in rows[begin:begin+size]],'count':count,'next':next_url}

@transaction.atomic
def environment_gate():
    row,_=EnvironmentState.objects.get_or_create(pk=1,defaults={'mode':settings.STEP_MODE,'provider':settings.PAYMENT_PROVIDER})
    require(row.mode==settings.STEP_MODE and row.provider==settings.PAYMENT_PROVIDER,'environment_mismatch','Test/canlı veya provider değişimi için ayrı STEP veritabanı gerekir.',503)

def encrypted_text(text):
    import base64,os
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    raw=os.environ.get('STEP_FIELD_ENCRYPTION_KEY','')
    require(bool(raw),'encryption_unconfigured','Hassas alan anahtarı yapılandırılmadı.',503)
    try:key=bytes.fromhex(raw)
    except ValueError:key=base64.urlsafe_b64decode(raw+'='*((-len(raw))%4))
    require(len(key)==32,'encryption_invalid','Geçerli 256-bit alan anahtarı gerekir.',503)
    nonce=os.urandom(12);return 'enc:'+base64.urlsafe_b64encode(nonce+AESGCM(key).encrypt(nonce,text.encode(),b'STEP-outbox-v1')).decode()

def decrypted_text(text):
    if not text.startswith('enc:'):return text
    import base64,os
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    raw=os.environ.get('STEP_FIELD_ENCRYPTION_KEY','')
    require(bool(raw),'encryption_unconfigured','Hassas alan anahtarı eksik.',503)
    try:key=bytes.fromhex(raw)
    except ValueError:key=base64.urlsafe_b64decode(raw+'='*((-len(raw))%4))
    blob=base64.urlsafe_b64decode(text[4:]);return AESGCM(key).decrypt(blob[:12],blob[12:],b'STEP-outbox-v1').decode()

def bank_digest(iban):
    import hmac,hashlib,re
    normalized=re.sub(r'\s+','',str(iban)).upper()
    require(bool(re.fullmatch(r'TR[0-9]{24}',normalized)),'iban_invalid','Geçerli TL Türkiye IBAN hesabı gerekir.',400)
    expanded=''.join(str(ord(c)-55) if c.isalpha() else c for c in normalized[4:]+normalized[:4])
    require(int(expanded)%97==1,'iban_invalid','IBAN doğrulama hanesi geçersiz.',400)
    return hmac.new(settings.SECRET_KEY.encode(),normalized.encode(),hashlib.sha256).hexdigest()

def job_asset_access(user,job):
    if not user or not user.is_authenticated:return False
    if user.pk==job.owner_id:return True
    if Application.objects.filter(job=job).filter(Q(student=user)|Q(team__leader=user)).exists():return True
    if Invitation.objects.filter(job=job,status__in=['pending','accepted']).filter(Q(student=user)|Q(team__leader=user)).exists():return True
    return Contract.objects.filter(application__job=job,workers__user=user).exists()
