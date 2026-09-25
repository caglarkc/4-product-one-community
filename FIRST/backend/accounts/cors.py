"""Exact-origin access for direct browser clients; no cookie authentication."""
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.cache import patch_vary_headers


class CorsMiddleware:
    methods = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'}
    headers = {'authorization', 'content-type', 'x-csrftoken'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/api/auth/'):
            return self.get_response(request)
        origin = request.headers.get('Origin', '')
        allowed = origin in settings.CORS_ALLOWED_ORIGINS
        preflight = request.method == 'OPTIONS' and 'Access-Control-Request-Method' in request.headers
        if origin and not allowed:
            response = JsonResponse({'detail': 'İstemci adresine izin verilmiyor.', 'code': 'origin_denied'}, status=403)
        elif preflight:
            requested = {value.strip().lower() for value in request.headers.get('Access-Control-Request-Headers', '').split(',') if value.strip()}
            if not allowed or request.headers['Access-Control-Request-Method'] not in self.methods or not requested.issubset(self.headers):
                response = HttpResponse(status=403)
            else:
                response = HttpResponse(status=204)
                response['Access-Control-Allow-Methods'] = ', '.join(sorted(self.methods))
                response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-CSRFToken'
                response['Access-Control-Max-Age'] = '600'
        else:
            response = self.get_response(request)
        patch_vary_headers(response, ['Origin'])
        if preflight:
            patch_vary_headers(response, ['Access-Control-Request-Method', 'Access-Control-Request-Headers'])
        if allowed:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Expose-Headers'] = 'X-First-Session'
        response['Cache-Control'] = 'no-store'
        return response
