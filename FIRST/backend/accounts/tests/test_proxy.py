import hashlib
import hmac
import time
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, TestCase, override_settings
from accounts import security
from accounts.proxy import validate_proxy_secret
from .fakes import FakeRedis

SECRET = 'test-proxy-secret-at-least-32-characters'


def assertion(ip='203.0.113.1', path='/api/auth/login/', method='POST', timestamp=None, secret=SECRET):
    timestamp = str(int(time.time())) if timestamp is None else timestamp
    message = '\n'.join((ip, timestamp, method, path))
    return {'HTTP_X_FIRST_CLIENT_IP': ip, 'HTTP_X_FIRST_CLIENT_TIME': timestamp,
            'HTTP_X_FIRST_CLIENT_SIGNATURE': hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()}


@override_settings(AUTH_PROXY_SECRET=SECRET)
class ProxyTests(TestCase):
    def setUp(self):
        self.fake = FakeRedis()
        patcher = patch('accounts.security.client', return_value=self.fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = Client(enforce_csrf_checks=True)

    def login(self, ip, email):
        token = self.client.get('/api/auth/csrf/', **assertion(ip, '/api/auth/csrf/', 'GET')).json()['csrfToken']
        return self.client.post('/api/auth/login/', {'email': email, 'password': 'bad'},
            content_type='application/json', HTTP_X_CSRFTOKEN=token, **assertion(ip))

    @override_settings(AUTH_IP_ATTEMPTS=1)
    def test_valid_assertions_give_distinct_client_rate_budgets(self):
        self.assertEqual(self.login('203.0.113.1', 'one@example.com').status_code, 400)
        self.assertEqual(self.login('203.0.113.2', 'two@example.com').status_code, 400)
        self.assertEqual(self.login('203.0.113.1', 'three@example.com').status_code, 429)
        self.assertEqual(security.attempts('password-ip', '203.0.113.1'), 2)
        self.assertEqual(security.attempts('password-ip', '203.0.113.2'), 1)
        self.assertEqual(security.attempts('password-ip', '127.0.0.1'), 0)

    def test_missing_assertions_rejected_for_all_auth_routes(self):
        for path in ['csrf/', 'me/', 'config/', 'register/', 'login/', 'logout/']:
            response = self.client.get('/api/auth/' + path)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()['code'], 'invalid_proxy_assertion')
            self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertEqual(self.client.get('/health/').status_code, 200)

    def test_forged_stale_future_method_and_path_assertions_rejected(self):
        good = assertion(path='/api/auth/csrf/', method='GET')
        cases = [good | {'HTTP_X_FIRST_CLIENT_SIGNATURE': '0' * 64},
                 good | {'HTTP_X_FIRST_CLIENT_IP': '203.0.113.8'},
                 assertion(path='/api/auth/csrf/', method='GET', timestamp=str(int(time.time()) - 61)),
                 assertion(path='/api/auth/csrf/', method='GET', timestamp=str(int(time.time()) + 61)),
                 assertion(path='/api/auth/me/', method='GET'),
                 assertion(path='/api/auth/csrf/', method='POST')]
        for headers in cases:
            self.assertEqual(self.client.get('/api/auth/csrf/', **headers).status_code, 403)

    def test_invalid_ip_or_timestamp_rejected_even_when_signed(self):
        for ip in ['203.0.113.1, 203.0.113.2', ' 203.0.113.1', 'not-an-ip', 'fe80::1%en0']:
            self.assertEqual(self.client.get('/api/auth/csrf/', **assertion(ip, '/api/auth/csrf/', 'GET')).status_code, 403)
        for timestamp in ['1.5', '-1', ' 123', 'x', '9' * 100]:
            self.assertEqual(self.client.get('/api/auth/csrf/', **assertion(path='/api/auth/csrf/', method='GET', timestamp=timestamp)).status_code, 403)

    def test_equivalent_ipv6_addresses_share_canonical_rate_budget(self):
        self.assertEqual(self.login('2001:db8::1', 'one@example.com').status_code, 400)
        self.assertEqual(self.login('2001:0db8:0000:0000:0000:0000:0000:0001', 'two@example.com').status_code, 400)
        self.assertEqual(security.attempts('password-ip', '2001:db8::1'), 2)

    @override_settings(AUTH_PROXY_SECRET='')
    def test_unconfigured_mode_ignores_all_unsigned_ip_headers(self):
        token = self.client.get('/api/auth/csrf/').json()['csrfToken']
        response = self.client.post('/api/auth/login/', {'email': 'one@example.com', 'password': 'bad'},
            content_type='application/json', HTTP_X_CSRFTOKEN=token,
            HTTP_X_FORWARDED_FOR='203.0.113.4', **assertion('203.0.113.5', secret='attacker'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(security.attempts('password-ip', '127.0.0.1'), 1)
        self.assertEqual(security.attempts('password-ip', '203.0.113.5'), 0)

    def test_short_configured_secret_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_proxy_secret('short')
        self.assertEqual(validate_proxy_secret(''), '')
        self.assertEqual(validate_proxy_secret(SECRET), SECRET)
