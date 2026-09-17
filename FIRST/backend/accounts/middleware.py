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
    def process_response(self, request, response):
        try:
            return super().process_response(request, response)
        except (SecurityUnavailable, UpdateError):
            return unavailable()
