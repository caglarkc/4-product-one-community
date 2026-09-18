import time
from urllib.parse import urlparse, parse_qs
from unittest.mock import patch, Mock
from django.test import Client, TestCase, override_settings
from allauth.socialaccount.models import SocialAccount
from accounts.google_views import exchange, GoogleError
from accounts.models import User, SessionRecord
from accounts import security
from . import test_auth


@override_settings(GOOGLE_ENABLED=True, GOOGLE_CLIENT_ID='test-client', GOOGLE_CLIENT_SECRET='test-secret',
                   GOOGLE_REDIRECT_URI='https://first.test/accounts/google/login/callback/')
class GoogleTests(TestCase):
    setUp = test_auth.AuthTests.setUp
    post = test_auth.AuthTests.post
    register = test_auth.AuthTests.register
    def start(self, **data):
        response = self.post('google/start', data)
        self.assertEqual(response.status_code, 200, response.content)
        return parse_qs(urlparse(response.json()['authorization_url']).query)

    def callback(self, params, claims=None, client=None):
        claims = claims or {'sub': 'google-123', 'email': 'new@gmail.com', 'email_verified': True, 'name': 'Google Member'}
        with patch('accounts.google_views.exchange', return_value=claims):
            return (client or self.client).get('/api/auth/google/callback/', {'state': params['state'][0], 'code': 'valid'})

    def signup_data(self, **extra):
        return {'username': 'google_member', 'full_name': 'Google Member', 'birth_date': '2000-01-01',
                'gender': 'unspecified', **extra}

    def test_new_signup_is_pending_then_no_password_and_no_email(self):
        from django.core import mail
        params = self.start(remember_me=True)
        self.assertEqual(params['code_challenge_method'], ['S256'])
        self.assertEqual(params['scope'], ['openid email profile'])
        self.assertEqual(self.callback(params).json()['status'], 'profile_required')
        self.assertEqual(User.objects.count(), 0)
        pending = self.client.get('/api/auth/google/signup/').json()
        self.assertFalse(pending['email_editable'])
        self.assertEqual(pending['profile']['full_name'], 'Google Member')
        result = self.post('google/signup', self.signup_data())
        self.assertEqual(result.status_code, 201, result.content)
        self.assertEqual(result.json()['user']['providers'], ['google'])
        self.assertFalse(result.json()['user']['has_usable_password'])
        self.assertTrue(result.json()['user']['email_verified'])
        self.assertAlmostEqual(result.cookies['sessionid']['max-age'], 30 * 86400, delta=2)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.post('google/signup', self.signup_data(username='another')).status_code, 400)

    def test_existing_verified_email_automatch_preserves_password(self):
        self.register(); user = User.objects.get(); user.email_verified = True; user.save()
        self.post('logout')
        claims = {'sub': 'existing', 'email': user.email, 'email_verified': True, 'hd': 'example.com'}
        result = self.callback(self.start(), claims)
        self.assertEqual(result.json()['status'], 'authenticated')
        user.refresh_from_db(); self.assertTrue(user.has_usable_password())
        self.assertEqual(SocialAccount.objects.get().user_id, user.pk)

    def test_unverified_takeover_revokes_sessions_password_and_tokens(self):
        self.register(); user = User.objects.get(); version = user.security_version
        old = SessionRecord.objects.get()
        other = Client(enforce_csrf_checks=True)
        self.client = other
        claims = {'sub': 'existing', 'email': user.email, 'email_verified': True, 'hd': 'example.com'}
        self.assertEqual(self.callback(self.start(), claims).status_code, 200)
        user.refresh_from_db(); old.refresh_from_db()
        self.assertFalse(user.has_usable_password()); self.assertTrue(old.revoked)
        self.assertEqual(user.security_version, version + 1)

    def test_untrusted_email_never_matches_existing(self):
        self.register(); self.post('logout')
        claims = {'sub': 'untrusted', 'email': self.data['email'], 'email_verified': True}
        self.assertEqual(self.callback(self.start(), claims).json()['status'], 'profile_required')
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])
        self.assertEqual(self.post('google/signup', self.signup_data()).status_code, 400)
        self.assertEqual(SocialAccount.objects.count(), 0)

    def test_missing_email_fallback_and_verification(self):
        from django.core import mail
        self.callback(self.start(), {'sub': 'missing'})
        self.assertEqual(self.post('google/signup', self.signup_data()).status_code, 400)
        result = self.post('google/signup', self.signup_data(email='new@example.com'))
        self.assertEqual(result.json()['code'], 'email_verification_required')
        self.assertEqual(User.objects.count(), 0)
        self.post('google/email/request', {'email': 'new@example.com'})
        self.assertEqual(self.post('google/email/verify', {'key': self.email_key()}).status_code, 200)
        result = self.post('google/signup', self.signup_data())
        self.assertEqual(result.status_code, 201, result.content)
        self.assertTrue(result.json()['user']['email_verified'])
        self.assertEqual(len(mail.outbox), 1)

    def test_validation_keeps_pending_and_rejects_password_email_tamper_age(self):
        self.callback(self.start())
        for extra in [{'password': 'Other9!pass'}, {'email': 'wrong@gmail.com'}, {'birth_date': '2025-01-01'}]:
            self.assertEqual(self.post('google/signup', self.signup_data(**extra)).status_code, 400)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(self.post('google/signup', self.signup_data()).status_code, 201)

    def test_callback_bound_to_browser_and_single_use(self):
        params = self.start()
        self.assertEqual(self.callback(params, client=Client()).status_code, 400)
        self.assertEqual(self.callback(params).status_code, 200)
        self.assertEqual(self.callback(params).status_code, 400)

    def test_expired_cancelled_and_duplicate_state(self):
        params = self.start()
        result = self.client.get('/api/auth/google/callback/', {'state': params['state'][0], 'error': 'access_denied'})
        self.assertEqual(result.json()['code'], 'google_cancelled')
        self.assertEqual(self.callback(params).status_code, 400)
        params = self.start(); security.consume_token('google-state', params['state'][0])
        self.assertEqual(self.callback(params).status_code, 400)
        self.assertEqual(self.client.get('/api/auth/google/callback/?state=a&state=b&code=c').status_code, 400)

    def test_sub_identity_wins_over_changed_email_and_disabled_rejected(self):
        self.callback(self.start()); self.post('google/signup', self.signup_data()); self.post('logout')
        user = User.objects.get()
        claims = {'sub': 'google-123', 'email': 'changed@gmail.com', 'email_verified': True}
        self.assertEqual(self.callback(self.start(), claims).json()['user']['id'], user.pk)
        self.post('logout'); user.is_active = False; user.save()
        self.assertEqual(self.callback(self.start(), claims).status_code, 400)

    def test_reauth_requires_same_linked_identity(self):
        self.assertEqual(self.post('google/start', {'purpose': 'reauth'}).status_code, 401)
        self.callback(self.start()); self.post('google/signup', self.signup_data())
        self.assertEqual(self.callback(self.start(purpose='reauth')).json()['status'], 'reauthenticated')
        result = self.callback(self.start(purpose='reauth'), {'sub': 'other', 'email': 'new@gmail.com', 'email_verified': True})
        self.assertEqual(result.status_code, 400)
        self.assertEqual(SocialAccount.objects.count(), 1)

    def test_csrf_and_disabled_configuration(self):
        self.assertEqual(self.client.post('/api/auth/google/start/', {}, content_type='application/json').status_code, 403)
        with override_settings(GOOGLE_ENABLED=False):
            self.assertFalse(self.client.get('/api/auth/config/').json()['providers']['google'])
            self.assertEqual(self.post('google/start').status_code, 503)

    def test_real_signed_token_validation_and_code_exchange(self):
        import jwt
        from cryptography.hazmat.primitives.asymmetric import rsa
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        now = int(time.time())
        claims = {'sub': 'signed', 'iss': 'https://accounts.google.com', 'aud': 'test-client',
                  'iat': now, 'exp': now + 600, 'nonce': 'expected'}
        flow = {'nonce': 'expected', 'verifier': 'pkce-test'}
        with patch('accounts.google_views.requests.post') as post, patch(
                'allauth.socialaccount.internal.jwtkit.fetch_key', return_value=('RS256', private.public_key())):
            post.return_value = Mock()
            for changed in [{}, {'aud': 'attacker'}, {'iss': 'https://evil.test'}, {'exp': now - 10}, {'nonce': 'wrong'}]:
                token = jwt.encode({**claims, **changed}, private, algorithm='RS256', headers={'kid': 'test'})
                post.return_value.json.return_value = {'id_token': token}
                if not changed:
                    self.assertEqual(exchange('code', flow)['sub'], 'signed')
                    self.assertEqual(post.call_args.kwargs['data']['code_verifier'], 'pkce-test')
                else:
                    with self.assertRaises(GoogleError):
                        exchange('code', flow)
            wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            post.return_value.json.return_value = {'id_token': jwt.encode(claims, wrong_key, algorithm='RS256')}
            with self.assertRaises(GoogleError):
                exchange('code', flow)

    def test_authoritative_recovery_removes_preexisting_attacker_identity(self):
        # Legacy unverified social account fixture: recovery must still remove it.
        user = User.objects.create_user(email='victim@gmail.com', username='legacy', full_name='Legacy')
        SocialAccount.objects.create(user=user, provider='google', uid='attacker')
        victim_id = user.pk
        self.assertEqual(self.callback(self.start(), {'sub': 'victim', 'email': 'victim@gmail.com',
            'email_verified': True}).json()['user']['id'], victim_id)
        self.assertFalse(SocialAccount.objects.filter(uid='attacker').exists())
        self.post('logout')
        self.assertEqual(self.callback(self.start(), {'sub': 'attacker', 'email': 'victim@gmail.com',
            'email_verified': False}).json()['status'], 'profile_required')
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])

    def email_key(self):
        from django.core import mail
        link = mail.outbox[-1].body.splitlines()[-1]
        return parse_qs(urlparse(link).query)['key'][0]

    def test_untrusted_existing_email_proof_required_then_matches(self):
        self.register(); user = User.objects.get(); self.post('logout')
        self.callback(self.start(), {'sub': 'thirdparty', 'email': user.email, 'email_verified': True})
        # Reset fixture mail interval created by normal registration.
        security.execute('delete', security.key('mail-interval', user.email))
        self.assertEqual(self.post('google/email/request', {'email': user.email}).status_code, 200)
        key = self.email_key()
        # Cross-browser proof is useless without its pending Google session.
        self.assertEqual(self.post('google/email/verify', {'key': key}, client=Client(enforce_csrf_checks=True)).status_code, 400)
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])
        result = self.post('google/email/verify', {'key': key})
        self.assertEqual(result.json()['status'], 'authenticated', result.content)
        self.assertEqual(result.json()['user']['id'], user.pk)
        self.assertFalse(result.json()['user']['has_usable_password'])
        self.assertEqual(self.post('google/email/verify', {'key': key}).status_code, 400)

    def test_new_email_proof_prefills_immutable_verified_signup(self):
        self.callback(self.start(), {'sub': 'missing-email'})
        self.assertEqual(self.post('google/email/request', {'email': 'new@example.com'}).status_code, 200)
        result = self.post('google/email/verify', {'key': self.email_key()})
        self.assertEqual(result.json()['status'], 'profile_required')
        pending = self.client.get('/api/auth/google/signup/').json()
        self.assertFalse(pending['email_editable']); self.assertTrue(pending['email_verified'])
        self.assertEqual(self.post('google/signup', self.signup_data(email='other@example.com')).status_code, 400)
        self.assertEqual(self.post('google/signup', self.signup_data()).status_code, 201)

    def test_email_proof_rejects_changed_security_version(self):
        self.register(); user = User.objects.get(); self.post('logout')
        self.callback(self.start(), {'sub': 'thirdparty', 'email': user.email})
        security.execute('delete', security.key('mail-interval', user.email))
        self.post('google/email/request', {'email': user.email})
        key = self.email_key()
        user.security_version += 1; user.save()
        self.assertEqual(self.post('google/email/verify', {'key': key}).status_code, 400)
        self.assertEqual(SocialAccount.objects.count(), 0)

    def test_reauth_token_requires_fresh_google_auth_time(self):
        import jwt
        from cryptography.hazmat.primitives.asymmetric import rsa
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        now = int(time.time())
        base = {'sub': 'signed', 'iss': 'https://accounts.google.com', 'aud': 'test-client',
                'iat': now, 'exp': now + 600, 'nonce': 'expected'}
        flow = {'nonce': 'expected', 'verifier': 'pkce', 'purpose': 'reauth', 'started_at': now}
        with patch('accounts.google_views.requests.post') as post, patch(
                'allauth.socialaccount.internal.jwtkit.fetch_key', return_value=('RS256', private.public_key())):
            post.return_value = Mock()
            for auth_time in [None, now - 120, now + 120, now]:
                claims = {**base, **({'auth_time': auth_time} if auth_time is not None else {})}
                post.return_value.json.return_value = {'id_token': jwt.encode(claims, private, algorithm='RS256')}
                if auth_time == now:
                    self.assertEqual(exchange('code', flow)['sub'], 'signed')
                else:
                    with self.assertRaises(GoogleError):
                        exchange('code', flow)

    def test_removed_identity_cannot_login_from_stale_prelock_read(self):
        self.callback(self.start()); self.post('google/signup', self.signup_data()); self.post('logout')
        user = User.objects.get()
        params = self.start()
        def recover_before_lock_return(**kwargs):
            SocialAccount.objects.filter(user=user).delete()
            return user
        with patch('accounts.google_views.User.objects.select_for_update') as lock:
            lock.return_value.get.side_effect = recover_before_lock_return
            result = self.callback(params)
        self.assertEqual(result.status_code, 400)
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])
