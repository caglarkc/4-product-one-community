"""Backend-owned, fixed destinations for OAuth UI responses."""
from urllib.parse import urlencode
from rest_framework.exceptions import ValidationError


def validate_callback_query(request):
    allowed = {'code', 'state', 'error'}
    if any(key not in allowed or len(request.query_params.getlist(key)) != 1 for key in request.query_params):
        raise ValidationError('Geçersiz OAuth dönüş parametreleri.')
    if len(request.query_params.get('error', '')) > 256:
        raise ValidationError('Geçersiz OAuth dönüş parametreleri.')


class OAuthDestinationMixin:
    oauth_provider = ''
    oauth_callback = False

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if not isinstance(getattr(response, 'data', None), dict):
            return response
        status = response.data.get('status')
        success = response.status_code < 400
        destination = None
        if success:
            if self.oauth_provider == 'github_app':
                if status == 'connected':
                    next_path = response.data.get('return_to')
                    if next_path not in ('/', '/hesap', '/projelerim/yeni'):
                        next_path = '/projelerim/yeni'
                    destination = '/github-kurulum?' + urlencode({'github': 'connected', 'next': next_path})
            else:
                provider = self.oauth_provider
                routes = {'profile_required': '/kayit/' + provider, 'reauthenticated': '/hesap'}
                routes['authenticated'] = '/github-kurulum?next=%2F' if provider == 'github' else '/'
                routes['linked'] = '/github-kurulum?next=%2Fhesap'
                destination = routes.get(status)
                if request.method == 'POST' and response.status_code == 201 and 'user' in response.data:
                    destination = routes['authenticated']
        elif self.oauth_callback:
            if self.oauth_provider == 'github_app':
                destination = '/github-kurulum?github=failed'
            else:
                error = 'cancelled' if request.query_params.get('error') == 'access_denied' else 'failed'
                destination = '/giris?' + urlencode({self.oauth_provider + '_error': error})
        if destination:
            response.data['redirect_to'] = destination
        response['Cache-Control'] = 'no-store'
        response['Referrer-Policy'] = 'no-referrer'
        return response
