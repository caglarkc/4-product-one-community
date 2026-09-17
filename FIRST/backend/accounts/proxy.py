"""Optional authenticated ingress assertion; unsigned headers never establish IP."""
import hashlib
import hmac
import ipaddress
import re
import time
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse


def validate_proxy_secret(secret):
    if secret and len(secret) < 32:
        raise ImproperlyConfigured('AUTH_PROXY_SECRET must contain at least 32 characters.')
    return secret


def client_ip(request):
    return getattr(request, 'auth_client_ip', request.META.get('REMOTE_ADDR', ''))


class TrustedClientIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.auth_client_ip = request.META.get('REMOTE_ADDR', '')
        if request.path.startswith('/api/auth/') and settings.AUTH_PROXY_SECRET:
            ip = request.headers.get('X-First-Client-IP', '')
            timestamp = request.headers.get('X-First-Client-Time', '')
            signature = request.headers.get('X-First-Client-Signature', '')
            valid = False
            try:
                # No lists, whitespace, IPv6 scope IDs or parser normalization
                # ambiguities are accepted. Signed text is used exactly as sent.
                if not ip or ip.strip() != ip or '%' in ip:
                    raise ValueError
                parsed_ip = ipaddress.ip_address(ip)
                if not re.fullmatch(r'[0-9]{1,12}', timestamp):
                    raise ValueError
                if abs(time.time() - int(timestamp)) > 60:
                    raise ValueError
                message = '\n'.join((ip, timestamp, request.method, request.path))
                expected = hmac.new(settings.AUTH_PROXY_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
                valid = hmac.compare_digest(expected, signature)
            except (ValueError, TypeError):
                pass
            if not valid:
                response = JsonResponse({'detail': 'Proxy güvenlik doğrulaması başarısız.',
                                         'code': 'invalid_proxy_assertion'}, status=403)
                response['Cache-Control'] = 'no-store'
                return response
            request.auth_client_ip = str(parsed_ip)
        return self.get_response(request)
