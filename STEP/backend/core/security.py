import hashlib
import re
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.views import exception_handler as drf_handler
from .models import DeviceCredential, RateWindow

class Problem(APIException):
    def __init__(self, code, detail, status=400, fields=None):
        self.status_code = status
        self.detail = {'code': code, 'detail': detail}
        if fields:
            self.detail['fields'] = fields

def require(condition, code='forbidden', detail='Bu işlem için yetkiniz yok.', status=403):
    if not condition:
        raise Problem(code, detail, status)

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

class DeviceAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = request.headers.get('Authorization', '')
        if not header:
            return None
        if not header.startswith('Bearer '):
            raise AuthenticationFailed('Invalid authorization scheme')
        token = DeviceCredential.objects.select_related('user').filter(digest=digest(header[7:]), revoked_at=None, expires_at__gt=timezone.now()).first()
        if not token or not token.user.is_active or token.password_digest != digest(token.user.password):
            raise AuthenticationFailed('Device credential expired or revoked')
        route = request.path.removeprefix('/api/v1/').strip('/')
        allowed = route == 'auth/logout' or re.fullmatch(r'tracker/(config|contracts|sessions|blocks|sessions/[0-9a-f-]+/stop)', route) or re.fullmatch(r'screenshots/[0-9a-f-]+/(image|publish|privacy|review-ready)', route)
        require(bool(allowed), 'device_scope', 'Cihaz kimliği yalnız takip ve kendi görüntü işlemlerinde kullanılabilir.')
        return token.user, token
    def authenticate_header(self, request):
        return 'Bearer'

def exception_handler(exc, context):
    response = drf_handler(exc, context)
    if response is not None and not isinstance(response.data, dict):
        response.data = {'code':'invalid', 'detail':str(response.data)}
    elif response is not None and 'code' not in response.data:
        response.data = {'code':'invalid', 'detail':str(response.data)}
    return response

def rate_limit(request, operation, maximum=12, seconds=300):
    # Security throttles are technical limits, not product credit policies.
    key = digest(operation + ':' + request.META.get('REMOTE_ADDR', 'unknown'))
    with transaction.atomic():
        row, _ = RateWindow.objects.get_or_create(key=key)
        row = RateWindow.objects.select_for_update().get(pk=row.pk)
        if row.starts_at + timedelta(seconds=seconds) <= timezone.now():
            row.starts_at, row.count = timezone.now(), 0
        require(row.count < maximum, 'rate_limited', 'Kısa süre içinde çok fazla deneme yapıldı.', 429)
        row.count += 1
        row.save()
