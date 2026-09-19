"""Client address from the protected nginx ingress, never from public assertions."""
import ipaddress
from django.conf import settings


def client_ip(request):
    return getattr(request, 'auth_client_ip', request.META.get('REMOTE_ADDR', ''))


class TrustedClientIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.auth_client_ip = request.META.get('REMOTE_ADDR', '')
        # Enable only with Docker bound to loopback and nginx overwriting X-Real-IP.
        if settings.TRUST_NGINX_PROXY:
            value = request.headers.get('X-Real-IP', '')
            try:
                if not value or value.strip() != value or '%' in value:
                    raise ValueError
                request.auth_client_ip = str(ipaddress.ip_address(value))
            except ValueError:
                pass
        return self.get_response(request)
