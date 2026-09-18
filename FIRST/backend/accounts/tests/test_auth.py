from datetime import date, timedelta
from unittest.mock import patch
from django.core import mail
from django.test import TestCase, Client, override_settings
from django.utils import timezone
import redis
from accounts.models import User, SessionRecord
from accounts import security
from .fakes import FakeRedis


class AuthTests(TestCase):
    def setUp(self):
        self.fake = FakeRedis()
        self.patch = patch('accounts.security.client', return_value=self.fake)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.client = Client(enforce_csrf_checks=True)
        self.data = {'email': 'member@example.com', 'username': 'Üye_1', 'full_name': 'Test Üye',
                     'birth_date': '2000-05-05', 'gender': 'unspecified', 'password': 'Özgün9!x'}

    def post(self, path, data=None, client=None):
        client = client or self.client
        csrf = client.get('/api/auth/csrf/').json()['csrfToken']
        return client.post('/api/auth/' + path + '/', data or {}, content_type='application/json', HTTP_X_CSRFTOKEN=csrf)

    def register(self):
        response = self.post('register', self.data)
        self.assertEqual(response.status_code, 201, response.content)
        return response

    def test_register_me_logout_and_login_unverified(self):
        response = self.register()
        self.assertFalse(response.json()['user']['email_verified'])
        self.assertTrue(response.cookies['sessionid']['httponly'])
        self.assertTrue(response.cookies['sessionid']['secure'])
        self.assertAlmostEqual(response.cookies['sessionid']['max-age'], 86400, delta=2)
        self.assertEqual(self.client.get('/api/auth/me/').json()['user']['email'], self.data['email'])
        self.assertEqual(self.post('logout').status_code, 200)
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])
        self.assertEqual(self.post('login', {'email': self.data['email'], 'password': self.data['password']}).status_code, 200)

    def test_remember_me_and_normal_expiries(self):
        self.register()
        self.post('logout')
        response = self.post('login', {'email': self.data['email'], 'password': self.data['password'], 'remember_me': True})
        self.assertAlmostEqual(response.cookies['sessionid']['max-age'], 30 * 86400, delta=2)
        self.assertLess(abs((SessionRecord.objects.latest('created_at').expires_at - timezone.now()).total_seconds() - 30 * 86400), 3)

    def test_csrf_required_for_anonymous_mutations(self):
        for path in ['register', 'login', 'logout']:
            with self.subTest(path=path):
                response = self.client.post('/api/auth/' + path + '/', self.data, content_type='application/json')
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()['code'], 'csrf_failed')
        self.assertEqual(User.objects.count(), 0)

    def test_wrong_csrf_and_cross_origin_rejected(self):
        token = self.client.get('/api/auth/csrf/').json()['csrfToken']
        for options in [{'HTTP_X_CSRFTOKEN': 'x' * 64}, {'HTTP_X_CSRFTOKEN': token, 'HTTP_ORIGIN': 'https://evil.test'}]:
            response = self.client.post('/api/auth/register/', self.data, content_type='application/json', **options)
            self.assertEqual(response.status_code, 403)

    def test_missing_required_fields(self):
        for field in self.data:
            data = self.data.copy()
            del data[field]
            with self.subTest(field=field):
                response = self.post('register', data)
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json()['errors'])

    def test_duplicate_casefold_username_and_lowercase_email(self):
        self.register()
        for overrides, field in [({'email': 'MEMBER@example.com', 'username': 'newuser'}, 'email'),
                                 ({'email': 'new@example.com', 'username': 'üYE_1'}, 'username')]:
            response = self.post('register', self.data | overrides)
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.json()['errors'])

    def test_age_boundary(self):
        today = date.today()
        birthday = today.replace(year=today.year - 13)
        response = self.post('register', self.data | {'birth_date': (birthday + timedelta(days=1)).isoformat()})
        self.assertEqual(response.status_code, 400)
        response = self.post('register', self.data | {'birth_date': birthday.isoformat()})
        self.assertEqual(response.status_code, 201)

    def test_password_policy_rejections(self):
        values = ['Abc1!xy', 'Abc1!' + 'x' * 16, 'abcdefgh1!', 'ABCDEFGH1!', 'Abcdefgh!', 'Abcdefgh1', 'Abc 1!xy', 'Abc\t1!xy', 'Abc\u00a01!xy', 'Password1!']
        for password in values:
            with self.subTest(password=password):
                response = self.post('register', self.data | {'password': password})
                self.assertEqual(response.status_code, 400)
                self.assertIn('password', response.json()['errors'])

    def test_password_lengths_8_and_20_and_turkish(self):
        for i, password in enumerate(['Özgün9!x', 'Özgün9!' + 'x' * 13]):
            response = self.post('register', self.data | {'email': f'{i}@example.com', 'username': f'user_{i}', 'password': password})
            self.assertEqual(response.status_code, 201, response.content)

    def test_generic_invalid_credentials_and_account_limit(self):
        self.register()
        self.post('logout')
        missing = self.post('login', {'email': 'missing@example.com', 'password': 'bad'}).json()
        for _ in range(5):
            response = self.post('login', {'email': self.data['email'], 'password': 'bad'})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), missing)
        response = self.post('login', {'email': self.data['email'], 'password': self.data['password']})
        self.assertEqual(response.status_code, 429)
        self.fake.expiry[security.key('password-account', self.data['email'])] = 0
        self.assertEqual(self.post('login', {'email': self.data['email'], 'password': self.data['password']}).status_code, 200)

    @override_settings(AUTH_IP_ATTEMPTS=2)
    def test_ip_limit_ignores_spoofed_forwarded_for(self):
        for i in range(2):
            self.assertEqual(self.post('login', {'email': f'{i}@example.com', 'password': 'bad'}).status_code, 400)
        self.assertEqual(self.post('login', {'email': 'other@example.com', 'password': 'bad'}).status_code, 429)

    def test_email_body_and_fixed_origin_and_token_privacy(self):
        response = self.register()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.data['email']])
        self.assertIn('https://first.test/eposta-dogrula?key=', mail.outbox[0].body)
        self.assertIn('24 saat', mail.outbox[0].body)
        token = mail.outbox[0].body.split('key=')[1]
        payload = security.peek_token('email-verify', token)
        self.assertEqual(payload['email'], self.data['email'])
        self.assertNotIn(token, str(response.json()))
        self.assertNotIn(token, ' '.join(self.fake.values.keys()))

    def test_smtp_failure_rolls_back_registration(self):
        with patch('accounts.views.send_mail', side_effect=OSError('secret SMTP credentials')):
            response = self.post('register', self.data)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'email_delivery_failed')
        self.assertNotIn('secret', response.content.decode())
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(SessionRecord.objects.count(), 0)

    def test_redis_failure_is_closed(self):
        with patch('accounts.security.client', side_effect=redis.ConnectionError('secret')):
            response = self.post('register', self.data)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.content.decode())
        self.assertEqual(User.objects.count(), 0)

    def test_unknown_sensitive_fields_and_invalid_shapes(self):
        for fields in [{'email_verified': True}, {'phone_verified': True}, {'providers': ['github']}, {'is_staff': True}]:
            self.assertEqual(self.post('register', self.data | fields).status_code, 400)
        self.assertEqual(self.post('register', ['invalid']).status_code, 400)
        self.assertEqual(self.post('login', {'email': 'a@example.com', 'password': 'x', 'remember_me': 'true'}).status_code, 400)

    def test_phone_is_never_verified(self):
        response = self.post('register', self.data | {'phone': '+90 (555) 123-4567'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['user']['phone'], '+905551234567')
        self.assertFalse(response.json()['user']['phone_verified'])

    def test_registry_revocation_and_security_version(self):
        self.register()
        SessionRecord.objects.update(revoked=True)
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])
        self.post('login', {'email': self.data['email'], 'password': self.data['password']})
        User.objects.update(security_version=2)
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])

    def test_expired_registry_prevents_access(self):
        self.register()
        SessionRecord.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])

    def test_response_allowlist_and_no_store_and_disabled_social(self):
        response = self.register()
        self.assertEqual(set(response.json()['user']), {'id', 'email', 'username', 'full_name', 'birth_date', 'gender', 'phone', 'email_verified', 'phone_verified', 'profile_complete', 'providers', 'connected_accounts', 'capabilities', 'has_usable_password'})
        for path in ['me', 'csrf', 'config']:
            self.assertEqual(self.client.get('/api/auth/' + path + '/')['Cache-Control'], 'no-store')
        self.assertEqual(self.client.get('/api/auth/config/').json()['providers'], {'google': False, 'github': False})


    def test_repeated_login_rotates_and_revokes_previous_session(self):
        self.register()
        old_cookie = self.client.cookies['sessionid'].value
        response = self.post('login', {'email': self.data['email'], 'password': self.data['password']})
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.client.cookies['sessionid'].value, old_cookie)
        self.assertTrue(SessionRecord.objects.get(key_hash=security.digest(old_cookie)).revoked)
        other = Client(enforce_csrf_checks=True)
        other.cookies['sessionid'] = old_cookie
        self.assertIsNone(other.get('/api/auth/me/').json()['user'])

    def test_inflight_password_proof_rejects_concurrent_attempt(self):
        owner = security.acquire_password_lock(self.data['email'])
        response = self.post('login', {'email': self.data['email'], 'password': self.data['password']})
        self.assertEqual(response.status_code, 429)
        security.release_password_lock(self.data['email'], owner)
        self.assertEqual(self.post('login', {'email': self.data['email'], 'password': self.data['password']}).status_code, 400)

    def test_redis_failure_with_authenticated_session_is_closed(self):
        self.register()
        with patch('accounts.security.client', side_effect=redis.ConnectionError('secret')):
            response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('secret', response.content.decode())

    def test_invalid_profile_values(self):
        for fields in [{'username': 'ab'}, {'username': 'x'*31}, {'username': 'bad-name'},
                       {'gender': ''}, {'phone': '05551234567'}, {'birth_date': 'not-date'},
                       {'full_name': ' '}, {'email': 'invalid'}]:
            with self.subTest(fields=fields):
                self.assertEqual(self.post('register', self.data | fields).status_code, 400)

    def test_database_email_constraint_blocks_case_variants(self):
        from django.db import IntegrityError, transaction
        self.register()
        user = User.objects.create_user(email='other@example.com', username='other', password='Özgün9!x')
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.filter(pk=user.pk).update(email=self.data['email'].upper())


    def test_deployment_breach_corpus_is_applied(self):
        with override_settings(AUTH_BREACHED_PASSWORD_HASHES=frozenset({security.digest(self.data['password'])})):
            response = self.post('register', self.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.json()['errors'])

    def test_invalid_explicit_breach_corpus_fails_configuration(self):
        import tempfile
        from pathlib import Path
        from django.core.exceptions import ImproperlyConfigured
        from accounts.password_corpus import load_corpus
        with tempfile.TemporaryDirectory() as folder:
            corpus = Path(folder) / 'hashes.txt'
            with self.assertRaises(ImproperlyConfigured):
                load_corpus(str(corpus))
            corpus.write_text('invalid-hash')
            with self.assertRaises(ImproperlyConfigured):
                load_corpus(str(corpus))
            corpus.write_text(security.digest('Özgün9!x') + '\n')
            self.assertEqual(load_corpus(str(corpus)), {security.digest('Özgün9!x')})


    def test_username_length_is_checked_after_nfc_normalization(self):
        response = self.post('register', self.data | {'username': 'a\u0301b'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.json()['errors'])
        self.assertEqual(User.objects.count(), 0)

    def test_decomposed_username_normalizing_to_max_length_is_accepted(self):
        username = 'a\u0301' * 30
        response = self.post('register', self.data | {'username': username})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()['user']['username'], 'á' * 30)
        self.assertEqual(User.objects.get().username, 'á' * 30)
