from django.http import JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from .models import SessionRecord
from .security import SecurityUnavailable, digest


def unavailable():
    response = JsonResponse({'detail': 'Kimlik hizmeti geçici olarak kullanılamıyor.', 'code': 'service_unavailable'}, status=503)
    response['Cache-Control'] = 'no-store'
    return response


class AuthBoundaryMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, SecurityUnavailable):
            return unavailable()

    def process_response(self, request, response):
        if request.path.startswith('/api/auth/'):
            response['Cache-Control'] = 'no-store'
        return response


class RegistryMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            if request.user.is_authenticated:
                valid = SessionRecord.objects.filter(user=request.user,
                    key_hash=digest(request.session.session_key), revoked=False,
                    security_version=request.user.security_version, expires_at__gt=timezone.now()).exists()
                if not valid:
                    from django.contrib.auth import logout
                    logout(request)
        except SecurityUnavailable:
            return unavailable()


from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.backends.base import UpdateError


class RedisSessionMiddleware(SessionMiddleware):
    """Transport the existing Redis session explicitly, never by browser cookie."""
    def process_request(self, request):
        import re
        value = request.headers.get('Authorization')
        if value is not None and not re.fullmatch(r'Bearer [a-z0-9]{32}', value):
            response = JsonResponse({'detail': 'Geçersiz oturum anahtarı.', 'code': 'invalid_session'}, status=401)
            response['X-First-Session'] = ''
            return response
        request.incoming_session_key = value[7:] if value else None
        request.session = self.SessionStore(request.incoming_session_key)
        try:
            # Resolve an expired/revoked key now, before auth/CSRF access.
            request.session.items()
            if value and not request.session.session_key:
                response = JsonResponse({'detail': 'Oturum süresi doldu. Yeniden giriş yapın.', 'code': 'invalid_session'}, status=401)
                response['X-First-Session'] = ''
                return response
        except SecurityUnavailable:
            return unavailable()

    def process_response(self, request, response):
        if not hasattr(request, 'session'):
            return response
        try:
            response = super().process_response(request, response)
            # Django's persistence/expiry semantics are retained; cookies are not
            # an authentication transport and must not be emitted to clients.
            from django.conf import settings
            response.cookies.pop(settings.SESSION_COOKIE_NAME, None)
            if response.status_code < 500 and request.session.session_key != request.incoming_session_key:
                response['X-First-Session'] = request.session.session_key or ''
            return response
        except (SecurityUnavailable, UpdateError):
            return unavailable()
