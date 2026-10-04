from unittest.mock import patch

from django.db import OperationalError
from django.test import Client, TestCase, override_settings

from core.models import EnvironmentState


WEB = 'https://step.ack-techs.com'


@override_settings(
    DEBUG=False, ALLOWED_HOSTS=['testserver'], STEP_MODE='live',
    PAYMENT_PROVIDER='iyzico_live', SECURE_SSL_REDIRECT=True,
    SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'),
    CORS_ALLOWED_ORIGINS=[WEB], CSRF_TRUSTED_ORIGINS=[WEB],
    EMAIL_HOST='', DEFAULT_FROM_EMAIL='',
)
class HostedBackendTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def csrf(self):
        return self.client.get('/api/v1/auth/csrf/', secure=True, HTTP_ORIGIN=WEB).json()['csrf_token']

    def post(self, route, payload, token=None, origin=WEB):
        headers = {'HTTP_ORIGIN': origin}
        if token:
            headers['HTTP_X_CSRFTOKEN'] = token
        return self.client.post('/api/v1/' + route + '/', payload,
                                content_type='application/json', secure=True, **headers)

    def test_health_checks_database_and_does_not_disclose_errors(self):
        self.assertEqual(self.client.get('/health/', secure=True).json(), {'status': 'ok'})
        with patch('config.health.connection.cursor', side_effect=OperationalError('private db detail')):
            response = self.client.get('/health/', secure=True)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unavailable'})

    def test_proxy_https_redirect_and_secure_csrf_cookie(self):
        self.assertEqual(self.client.get('/health/').status_code, 301)
        self.assertEqual(self.client.get('/health/', HTTP_X_FORWARDED_PROTO='https').status_code, 200)
        self.csrf()
        cookie = self.client.cookies['step_csrf']
        self.assertTrue(cookie['secure'])
        self.assertEqual(cookie['samesite'], 'Lax')

    def test_cors_allows_only_the_production_frontend(self):
        good = self.client.options('/api/v1/auth/login/', secure=True, HTTP_ORIGIN=WEB,
                                   HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
                                   HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type,x-csrftoken,idempotency-key')
        self.assertEqual(good['Access-Control-Allow-Origin'], WEB)
        self.assertEqual(good['Access-Control-Allow-Credentials'], 'true')
        bad = self.client.options('/api/v1/auth/login/', secure=True,
                                  HTTP_ORIGIN='https://untrusted.example',
                                  HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST')
        self.assertNotIn('Access-Control-Allow-Origin', bad)

    def test_login_rejects_missing_csrf_and_foreign_origin(self):
        payload = {'email': 'missing@example.invalid', 'password': 'irrelevant'}
        self.assertEqual(self.post('auth/login', payload).status_code, 403)
        self.assertEqual(self.post('auth/login', payload, self.csrf(),
                                  origin='https://untrusted.example').status_code, 403)

    def test_registration_session_me_and_logout(self):
        response = self.post('auth/register', {
            'email': 'hosting-check@example.invalid',
            'password': 'TemporaryCheck-4pJx8k',
            'display_name': 'Disposable hosting check', 'roles': ['student'],
        }, self.csrf())
        self.assertEqual(response.status_code, 200)
        session = self.client.cookies['step_session']
        self.assertTrue(session['secure'])
        self.assertTrue(session['httponly'])
        self.assertEqual(session['samesite'], 'Lax')
        self.assertEqual(self.client.get('/api/v1/auth/me/', secure=True).status_code, 200)
        self.assertEqual(self.post('auth/logout', {}, self.csrf()).status_code, 204)
        self.assertEqual(self.client.get('/api/v1/auth/me/', secure=True).status_code, 401)

    def test_live_mode_reports_unavailable_payments_and_mail(self):
        config = self.client.get('/api/v1/config/', secure=True).json()
        self.assertEqual(config['mode'], 'live')
        self.assertTrue(config['verification_required'])
        self.assertFalse(config['payment_ready'])
        self.assertFalse(config['payout_ready'])
        self.assertEqual(self.post('auth/password-reset', {'email': 'missing@example.invalid'},
                                  self.csrf()).status_code, 503)

    def test_existing_test_database_cannot_be_used_in_live_mode(self):
        EnvironmentState.objects.create(pk=1, mode='test', provider='simulator')
        response = self.client.get('/api/v1/config/', secure=True)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'environment_mismatch')

    def test_proxy_clients_have_separate_login_limits(self):
        token = self.csrf()
        payload = {'email': 'missing@example.invalid', 'password': 'irrelevant'}
        def attempt(address):
            return self.client.post('/api/v1/auth/login/', payload, content_type='application/json',
                                    secure=True, HTTP_ORIGIN=WEB, HTTP_X_CSRFTOKEN=token,
                                    HTTP_X_REAL_IP=address).status_code
        for _ in range(12):
            self.assertEqual(attempt('192.0.2.1'), 401)
        self.assertEqual(attempt('192.0.2.1'), 429)
        self.assertEqual(attempt('192.0.2.2'), 401)

    @override_settings(SECURE_PROXY_SSL_HEADER=None)
    def test_direct_deployment_ignores_spoofed_client_ip(self):
        token = self.csrf()
        for index in range(13):
            response = self.client.post('/api/v1/auth/login/',
                                        {'email': 'missing@example.invalid', 'password': 'irrelevant'},
                                        content_type='application/json', secure=True, HTTP_ORIGIN=WEB,
                                        HTTP_X_CSRFTOKEN=token, HTTP_X_REAL_IP=f'192.0.2.{index + 1}')
            self.assertEqual(response.status_code, 401 if index < 12 else 429)
