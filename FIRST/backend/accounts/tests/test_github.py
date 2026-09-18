import time
from urllib.parse import urlparse, parse_qs
from unittest.mock import patch, Mock
from django.test import Client, TestCase, override_settings
from allauth.socialaccount.models import SocialAccount
from accounts.github_views import exchange, GitHubError
from accounts.models import User, SessionRecord
from accounts import security
from . import test_auth


@override_settings(GITHUB_ENABLED=True, GITHUB_CLIENT_ID='test-client', GITHUB_CLIENT_SECRET='test-secret',
                   GITHUB_REDIRECT_URI='https://first.test/accounts/github/login/callback/')
class GitHubTests(TestCase):
    setUp = test_auth.AuthTests.setUp
    post = test_auth.AuthTests.post
    register = test_auth.AuthTests.register
    def start(self, **data):
        response = self.post('github/start', data)
        self.assertEqual(response.status_code, 200, response.content)
        return parse_qs(urlparse(response.json()['authorization_url']).query)

    def callback(self, params, claims=None, client=None):
        claims = claims or {'id': 100, 'verified_primary_email': 'new@gmail.com', 'name': 'GitHub Member'}
        with patch('accounts.github_views.exchange', return_value=claims):
            return (client or self.client).get('/api/auth/github/callback/', {'state': params['state'][0], 'code': 'valid'})

    def signup_data(self, **extra):
        return {'username': 'github_member', 'full_name': 'GitHub Member', 'birth_date': '2000-01-01',
                'gender': 'unspecified', **extra}

    def test_new_signup_is_pending_then_no_password_and_no_email(self):
        from django.core import mail
        params = self.start(remember_me=True)
        self.assertEqual(params['code_challenge_method'], ['S256'])
        self.assertEqual(params['scope'], ['user:email'])
        self.assertEqual(self.callback(params).json()['status'], 'profile_required')
        self.assertEqual(User.objects.count(), 0)
        pending = self.client.get('/api/auth/github/signup/').json()
        self.assertFalse(pending['email_editable'])
        self.assertEqual(pending['profile']['full_name'], 'GitHub Member')
        result = self.post('github/signup', self.signup_data())
        self.assertEqual(result.status_code, 201, result.content)
        self.assertEqual(result.json()['user']['providers'], ['github'])
        self.assertFalse(result.json()['user']['has_usable_password'])
        self.assertTrue(result.json()['user']['email_verified'])
        self.assertAlmostEqual(result.cookies['sessionid']['max-age'], 30 * 86400, delta=2)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.post('github/signup', self.signup_data(username='another')).status_code, 400)

    def test_existing_verified_email_automatch_preserves_password(self):
        self.register(); user = User.objects.get(); user.email_verified = True; user.save()
        self.post('logout')
        claims = {'id': 101, 'verified_primary_email': user.email}
        result = self.callback(self.start(), claims)
        self.assertEqual(result.json()['status'], 'authenticated')
        user.refresh_from_db(); self.assertTrue(user.has_usable_password())
        self.assertEqual(SocialAccount.objects.get().user_id, user.pk)

    def test_unverified_takeover_revokes_sessions_password_and_tokens(self):
        self.register(); user = User.objects.get(); version = user.security_version
        old = SessionRecord.objects.get()
        other = Client(enforce_csrf_checks=True)
        self.client = other
        claims = {'id': 101, 'verified_primary_email': user.email}
        self.assertEqual(self.callback(self.start(), claims).status_code, 200)
        user.refresh_from_db(); old.refresh_from_db()
        self.assertFalse(user.has_usable_password()); self.assertTrue(old.revoked)
        self.assertEqual(user.security_version, version + 1)

    def test_untrusted_email_never_matches_existing(self):
        self.register(); self.post('logout')
        claims = {'id': 102, 'email': self.data['email'], 'email_verified': True}
        self.assertEqual(self.callback(self.start(), claims).json()['status'], 'profile_required')
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])
        self.assertEqual(self.post('github/signup', self.signup_data()).status_code, 400)
        self.assertEqual(SocialAccount.objects.count(), 0)

    def test_missing_email_fallback_and_verification(self):
        from django.core import mail
        self.callback(self.start(), {'id': 103})
        self.assertEqual(self.post('github/signup', self.signup_data()).status_code, 400)
        result = self.post('github/signup', self.signup_data(email='new@example.com'))
        self.assertEqual(result.json()['code'], 'email_verification_required')
        self.assertEqual(User.objects.count(), 0)
        self.post('github/email/request', {'email': 'new@example.com'})
        self.assertEqual(self.post('github/email/verify', {'key': self.email_key()}).status_code, 200)
        result = self.post('github/signup', self.signup_data())
        self.assertEqual(result.status_code, 201, result.content)
        self.assertTrue(result.json()['user']['email_verified'])
        self.assertEqual(len(mail.outbox), 1)

    def test_validation_keeps_pending_and_rejects_password_email_tamper_age(self):
        self.callback(self.start())
        for extra in [{'password': 'Other9!pass'}, {'email': 'wrong@gmail.com'}, {'birth_date': '2025-01-01'}]:
            self.assertEqual(self.post('github/signup', self.signup_data(**extra)).status_code, 400)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(self.post('github/signup', self.signup_data()).status_code, 201)

    def test_callback_bound_to_browser_and_single_use(self):
        params = self.start()
        self.assertEqual(self.callback(params, client=Client()).status_code, 400)
        self.assertEqual(self.callback(params).status_code, 200)
        self.assertEqual(self.callback(params).status_code, 400)

    def test_expired_cancelled_and_duplicate_state(self):
        params = self.start()
        result = self.client.get('/api/auth/github/callback/', {'state': params['state'][0], 'error': 'access_denied'})
        self.assertEqual(result.json()['code'], 'github_cancelled')
        self.assertEqual(self.callback(params).status_code, 400)
        params = self.start(); security.consume_token('github-state', params['state'][0])
        self.assertEqual(self.callback(params).status_code, 400)
        self.assertEqual(self.client.get('/api/auth/github/callback/?state=a&state=b&code=c').status_code, 400)

    def test_sub_identity_wins_over_changed_email_and_disabled_rejected(self):
        self.callback(self.start()); self.post('github/signup', self.signup_data()); self.post('logout')
        user = User.objects.get()
        claims = {'id': 100, 'verified_primary_email': 'changed@gmail.com'}
        self.assertEqual(self.callback(self.start(), claims).json()['user']['id'], user.pk)
        self.post('logout'); user.is_active = False; user.save()
        self.assertEqual(self.callback(self.start(), claims).status_code, 400)

    def test_csrf_and_disabled_configuration(self):
        self.assertEqual(self.client.post('/api/auth/github/start/', {}, content_type='application/json').status_code, 403)
        with override_settings(GITHUB_ENABLED=False):
            self.assertFalse(self.client.get('/api/auth/config/').json()['providers']['github'])
            self.assertEqual(self.post('github/start').status_code, 503)

    def test_authoritative_recovery_removes_preexisting_attacker_identity(self):
        # Legacy unverified social account fixture: recovery must still remove it.
        user = User.objects.create_user(email='victim@gmail.com', username='legacy', full_name='Legacy')
        SocialAccount.objects.create(user=user, provider='github', uid='105')
        victim_id = user.pk
        self.assertEqual(self.callback(self.start(), {'id': 104, 'verified_primary_email': 'victim@gmail.com'}).json()['user']['id'], victim_id)
        self.assertFalse(SocialAccount.objects.filter(uid='105').exists())
        self.post('logout')
        self.assertEqual(self.callback(self.start(), {'id': 105, 'email': 'victim@gmail.com',
            'email_verified': False}).json()['status'], 'profile_required')
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])

    def email_key(self):
        from django.core import mail
        link = mail.outbox[-1].body.splitlines()[-1]
        return parse_qs(urlparse(link).query)['key'][0]

    def test_untrusted_existing_email_proof_required_then_matches(self):
        self.register(); user = User.objects.get(); self.post('logout')
        self.callback(self.start(), {'id': 106, 'email': user.email})
        # Reset fixture mail interval created by normal registration.
        security.execute('delete', security.key('mail-interval', user.email))
        self.assertEqual(self.post('github/email/request', {'email': user.email}).status_code, 200)
        key = self.email_key()
        # Cross-browser proof is useless without its pending GitHub session.
        self.assertEqual(self.post('github/email/verify', {'key': key}, client=Client(enforce_csrf_checks=True)).status_code, 400)
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])
        result = self.post('github/email/verify', {'key': key})
        self.assertEqual(result.json()['status'], 'authenticated', result.content)
        self.assertEqual(result.json()['user']['id'], user.pk)
        self.assertFalse(result.json()['user']['has_usable_password'])
        self.assertEqual(self.post('github/email/verify', {'key': key}).status_code, 400)

    def test_new_email_proof_prefills_immutable_verified_signup(self):
        self.callback(self.start(), {'id': 107})
        self.assertEqual(self.post('github/email/request', {'email': 'new@example.com'}).status_code, 200)
        result = self.post('github/email/verify', {'key': self.email_key()})
        self.assertEqual(result.json()['status'], 'profile_required')
        pending = self.client.get('/api/auth/github/signup/').json()
        self.assertFalse(pending['email_editable']); self.assertTrue(pending['email_verified'])
        self.assertEqual(self.post('github/signup', self.signup_data(email='other@example.com')).status_code, 400)
        self.assertEqual(self.post('github/signup', self.signup_data()).status_code, 201)

    def test_email_proof_rejects_changed_security_version(self):
        self.register(); user = User.objects.get(); self.post('logout')
        self.callback(self.start(), {'id': 106, 'email': user.email})
        security.execute('delete', security.key('mail-interval', user.email))
        self.post('github/email/request', {'email': user.email})
        key = self.email_key()
        user.security_version += 1; user.save()
        self.assertEqual(self.post('github/email/verify', {'key': key}).status_code, 400)
        self.assertEqual(SocialAccount.objects.count(), 0)

    def test_removed_identity_cannot_login_from_stale_prelock_read(self):
        self.callback(self.start()); self.post('github/signup', self.signup_data()); self.post('logout')
        user = User.objects.get()
        params = self.start()
        def recover_before_lock_return(**kwargs):
            SocialAccount.objects.filter(user=user).delete()
            return user
        with patch('accounts.github_views.User.objects.select_for_update') as lock:
            lock.return_value.get.side_effect = recover_before_lock_return
            result = self.callback(params)
        self.assertEqual(result.status_code, 400)
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])

    def test_link_requires_recent_session_and_rejects_conflict(self):
        self.assertEqual(self.post('github/start', {'purpose': 'link'}).status_code, 401)
        self.register()
        user = User.objects.get()
        result = self.callback(self.start(purpose='link'))
        self.assertEqual(result.json()['status'], 'linked', result.content)
        self.assertEqual(SocialAccount.objects.get().user_id, user.pk)
        self.assertEqual(self.callback(self.start(purpose='link'), {'id': 999}).status_code, 400)
        session = self.client.session
        session['reauthenticated_at'] = time.time() - 601
        session.save()
        self.assertEqual(self.post('github/start', {'purpose': 'link'}).status_code, 403)

    def test_link_rechecks_recent_authentication_at_callback(self):
        self.register()
        params = self.start(purpose='link')
        session = self.client.session
        session['reauthenticated_at'] = 0
        session.save()
        self.assertEqual(self.callback(params).status_code, 403)
        self.assertEqual(SocialAccount.objects.count(), 0)

    def test_cross_account_link_does_not_transfer(self):
        self.register()
        other = User.objects.create_user(username='other', email='other@example.com')
        SocialAccount.objects.create(user=other, provider='github', uid='100')
        self.assertEqual(self.callback(self.start(purpose='link')).status_code, 400)
        self.assertEqual(SocialAccount.objects.get().user_id, other.pk)

    def test_login_does_not_fake_recent_reauthentication(self):
        self.callback(self.start())
        self.post('github/signup', self.signup_data())
        self.assertNotIn('reauthenticated_at', self.client.session)
        self.assertEqual(self.post('github/start', {'purpose': 'reauth'}).json()['code'], 'github_reauth_unavailable')
        self.post('logout')
        self.callback(self.start())
        self.assertNotIn('reauthenticated_at', self.client.session)

    def test_exchange_uses_pkce_and_primary_verified_email_only(self):
        with patch('accounts.github_views.requests.post') as post, patch('accounts.github_views.requests.get') as get:
            post.return_value = Mock(status_code=200)
            post.return_value.json.return_value = {'access_token': 'secret', 'token_type': 'bearer'}
            profile = Mock(status_code=200)
            profile.json.return_value = {'id': 45, 'email': 'public@untrusted.test', 'login': 'sample-name'}
            emails = Mock(status_code=200)
            emails.json.return_value = [
                {'email': 'unverified@example.com', 'primary': True, 'verified': False},
                {'email': 'secondary@example.com', 'primary': False, 'verified': True},
                {'email': 'primary@example.com', 'primary': True, 'verified': True}]
            get.side_effect = [profile, emails]
            self.assertEqual(exchange('code', {'verifier': 'pkce'})['verified_primary_email'], 'primary@example.com')
            self.assertEqual(post.call_args.kwargs['data']['code_verifier'], 'pkce')
            self.assertFalse(post.call_args.kwargs['allow_redirects'])
            self.assertEqual(get.call_args_list[0].args[0], 'https://api.github.com/user')
            emails.json.return_value = []
            get.side_effect = [profile, emails]
            self.assertEqual(exchange('code', {'verifier': 'pkce'})['verified_primary_email'], '')
            profile.json.return_value = {'id': 'invalid'}
            get.side_effect = [profile]
            with self.assertRaises(GitHubError):
                exchange('code', {'verifier': 'pkce'})
            post.return_value.json.return_value = {'error': 'bad_verification_code'}
            with self.assertRaises(GitHubError):
                exchange('code', {'verifier': 'pkce'})

    def test_link_rejects_rotated_session_even_with_preserved_binder(self):
        self.register()
        params = self.start(purpose='link')
        session = self.client.session
        session.cycle_key()
        session.save()
        self.client.cookies['sessionid'] = session.session_key
        # Keep the rotated session valid so the OAuth session binding itself is exercised.
        SessionRecord.objects.update(key_hash=security.digest(session.session_key))
        self.assertEqual(self.callback(params).status_code, 400)
        self.assertEqual(SocialAccount.objects.count(), 0)

    def test_email_match_does_not_add_second_github_identity(self):
        self.register()
        user = User.objects.get()
        user.email_verified = True
        user.save()
        SocialAccount.objects.create(user=user, provider='github', uid='old')
        self.post('logout')
        result = self.callback(self.start(), {'id': 999, 'verified_primary_email': user.email})
        self.assertEqual(result.json()['code'], 'github_link_conflict')
        self.assertEqual(SocialAccount.objects.get().uid, 'old')
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])

    def test_link_is_idempotent_and_keeps_first_email(self):
        self.register()
        original_email = User.objects.get().email
        self.assertEqual(self.callback(self.start(purpose='link')).json()['status'], 'linked')
        self.assertEqual(self.callback(self.start(purpose='link')).json()['status'], 'linked')
        self.assertEqual(SocialAccount.objects.count(), 1)
        self.assertEqual(User.objects.get().email, original_email)

    def test_link_rejects_security_version_changed_after_start(self):
        self.register()
        params = self.start(purpose='link')
        user = User.objects.get()
        user.security_version += 1
        user.save(update_fields=['security_version'])
        # Preserve this current session, as a credential operation may do, while
        # invalidating the previously issued OAuth authorization flow.
        SessionRecord.objects.update(security_version=user.security_version)
        self.assertEqual(self.callback(params).status_code, 400)
        self.assertEqual(SocialAccount.objects.count(), 0)
        self.assertEqual(self.client.get('/api/auth/me/').json()['user']['id'], user.pk)
