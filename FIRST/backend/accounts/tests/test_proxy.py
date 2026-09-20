from unittest.mock import patch
from django.test import TestCase, override_settings
from accounts import security
from .fakes import FakeRedis, BearerClient as Client


def assertion(ip='203.0.113.1', *args, **kwargs):
    # Test nginx ingress, which overwrites X-Real-IP on the loopback backend.
    return {'HTTP_X_REAL_IP': ip}


@override_settings(TRUST_NGINX_PROXY=True)
class ProxyTests(TestCase):
    def setUp(self):
        self.fake = FakeRedis()
        patcher = patch('accounts.security.client', return_value=self.fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = Client(enforce_csrf_checks=True)

    def login(self, ip, email):
        token = self.client.get('/api/auth/csrf/').json()['csrfToken']
        return self.client.post('/api/auth/login/', {'email': email, 'password': 'bad'},
            content_type='application/json', HTTP_X_CSRFTOKEN=token, **assertion(ip))

    @override_settings(AUTH_IP_ATTEMPTS=1)
    def test_trusted_ingress_separates_rate_budgets(self):
        self.assertEqual(self.login('203.0.113.1', 'one@example.com').status_code, 400)
        self.assertEqual(self.login('203.0.113.2', 'two@example.com').status_code, 400)
        self.assertEqual(self.login('203.0.113.1', 'three@example.com').status_code, 429)
        self.assertEqual(security.attempts('password-ip', '203.0.113.1'), 2)
        self.assertEqual(security.attempts('password-ip', '203.0.113.2'), 1)

    def test_invalid_ip_falls_back_to_peer(self):
        for index, ip in enumerate(['203.0.113.1, 203.0.113.2', ' 203.0.113.1', 'not-an-ip', 'fe80::1%en0']):
            self.assertEqual(self.login(ip, f'{index}@example.com').status_code, 400)
        self.assertEqual(security.attempts('password-ip', '127.0.0.1'), 4)

    def test_equivalent_ipv6_addresses_share_canonical_rate_budget(self):
        self.assertEqual(self.login('2001:db8::1', 'one@example.com').status_code, 400)
        self.assertEqual(self.login('2001:0db8:0000:0000:0000:0000:0000:0001', 'two@example.com').status_code, 400)
        self.assertEqual(security.attempts('password-ip', '2001:db8::1'), 2)

    @override_settings(TRUST_NGINX_PROXY=False)
    def test_untrusted_mode_ignores_forwarded_and_legacy_headers(self):
        token = self.client.get('/api/auth/csrf/').json()['csrfToken']
        response = self.client.post('/api/auth/login/', {'email': 'one@example.com', 'password': 'bad'},
            content_type='application/json', HTTP_X_CSRFTOKEN=token, HTTP_X_REAL_IP='203.0.113.3',
            HTTP_X_FORWARDED_FOR='203.0.113.4', HTTP_X_FIRST_CLIENT_IP='203.0.113.5',
            HTTP_X_FIRST_CLIENT_SIGNATURE='attacker')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(security.attempts('password-ip', '127.0.0.1'), 1)
        self.assertEqual(security.attempts('password-ip', '203.0.113.5'), 0)

    @override_settings(CORS_ALLOWED_ORIGINS=['https://first.test'])
    def test_cors_preflight_allowlists_origin_headers_and_methods(self):
        allowed = self.client.options('/api/auth/projects/', HTTP_ORIGIN='https://first.test',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='authorization,content-type,x-csrftoken')
        self.assertEqual(allowed.status_code, 204)
        self.assertEqual(allowed['Access-Control-Allow-Origin'], 'https://first.test')
        self.assertNotIn('Access-Control-Allow-Credentials', allowed)
        for origin, headers in [('https://evil.test', 'authorization'), ('https://first.test', 'x-evil')]:
            result = self.client.options('/api/auth/projects/', HTTP_ORIGIN=origin,
                HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST', HTTP_ACCESS_CONTROL_REQUEST_HEADERS=headers)
            self.assertEqual(result.status_code, 403)
