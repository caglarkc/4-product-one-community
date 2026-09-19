import time
from datetime import timedelta
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse
from allauth.socialaccount.models import SocialAccount
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from accounts import security
from accounts.models import User, SessionRecord
from accounts.tests import test_auth
from projects import github
from projects.models import Project, GitHubCredential
from projects.tests import CONFIG, TOKENS, REPO


@override_settings(**CONFIG)
class ResetControlTests(TestCase):
    post = test_auth.AuthTests.post
    register = test_auth.AuthTests.register

    def setUp(self):
        test_auth.AuthTests.setUp(self)
        self.register()
        self.user = User.objects.get()
        self.user.email_verified = True
        self.user.save()
        self.account = SocialAccount.objects.create(user=self.user, provider='github', uid='77')
        self.project = Project.objects.create(owner=self.user, repository_id=99, installation_id=11,
                                             title='Owned', category='software')

    def delete(self, confirmation='HESABIMI SIL', client=None, **extra):
        client = client or self.client
        csrf = client.get('/api/auth/csrf/').json()['csrfToken']
        return client.delete('/api/auth/account/', {'confirmation': confirmation, **extra},
                             content_type='application/json', HTTP_X_CSRFTOKEN=csrf)

    def disconnect(self, repo=False):
        return self.post('projects/github/disconnect' if repo else 'github/disconnect',
                         {'confirmation': 'REPO' if repo else 'GITHUB'})

    def test_csrf_auth_recent_and_confirmation(self):
        for path in ('github/disconnect', 'projects/github/disconnect'):
            self.assertEqual(self.client.post('/api/auth/' + path + '/', {}, content_type='application/json').status_code, 403)
            self.assertEqual(self.post(path, {'confirmation': 'WRONG'}).status_code, 400)
            self.assertEqual(self.post(path, {'confirmation': 'REPO', 'user_id': 1}).status_code, 400)
        self.assertEqual(self.client.delete('/api/auth/account/', {}, content_type='application/json').status_code, 403)
        self.assertEqual(self.delete('wrong').status_code, 400)
        session = self.client.session
        session['reauthenticated_at'] = time.time() - 601
        session.save()
        for response in (self.disconnect(), self.disconnect(True), self.delete()):
            self.assertEqual(response.status_code, 403, response.content)
            self.assertEqual(response.json()['code'], 'reauthentication_required')
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.post('logout')
        for response in (self.disconnect(), self.disconnect(True), self.delete()):
            self.assertEqual(response.status_code, 401)

    def test_identity_disconnect_preserves_current_revokes_other_sessions_and_tokens(self):
        other = Client(enforce_csrf_checks=True)
        self.post('login', {'email': self.data['email'], 'password': self.data['password']}, client=other)
        token = security.issue_token('password-reset', {'user_id': self.user.pk, 'email': self.user.email,
                                                      'security_version': self.user.security_version}, 600)
        response = self.disconnect()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(SocialAccount.objects.filter(pk=self.account.pk).exists())
        self.project.refresh_from_db()
        self.assertFalse(self.project.is_active)
        self.assertIsNotNone(self.client.get('/api/auth/me/').json()['user'])
        self.assertIsNone(other.get('/api/auth/me/').json()['user'])
        response = self.post('password/reset/confirm', {'uid': str(self.user.pk), 'token': token, 'password': 'NewPass9!'})
        self.assertEqual(response.status_code, 400)

    def test_last_method_guard_and_other_provider(self):
        self.user.set_unusable_password(); self.user.save()
        # Keep the established test session consistent with the changed auth hash.
        session = self.client.session
        session['_auth_user_hash'] = self.user.get_session_auth_hash()
        session.save()
        response = self.disconnect()
        self.assertEqual(response.status_code, 403, response.content)
        self.assertEqual(response.json()['code'], 'last_login_method')
        self.assertTrue(SocialAccount.objects.filter(pk=self.account.pk).exists())
        SocialAccount.objects.create(user=self.user, provider='google', uid='google-user')
        self.assertEqual(self.disconnect().status_code, 200)
        self.assertTrue(SocialAccount.objects.filter(user=self.user, provider='google').exists())

    @patch('projects.github.requests.delete', return_value=Mock(status_code=204))
    def test_repo_disconnect_revokes_grant_and_preserves_identity(self, delete):
        github.save_tokens(self.account, TOKENS)
        response = self.disconnect(True)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(SocialAccount.objects.filter(pk=self.account.pk).exists())
        self.assertFalse(GitHubCredential.objects.exists())
        self.project.refresh_from_db(); self.assertFalse(self.project.is_active)
        self.assertEqual(delete.call_args.args[0], 'https://api.github.com/applications/app-client/grant')
        self.assertEqual(delete.call_args.kwargs['auth'], ('app-client', 'app-secret'))
        self.assertEqual(delete.call_args.kwargs['json'], {'access_token': TOKENS['access_token']})
        self.assertFalse(delete.call_args.kwargs['allow_redirects'])
        self.assertTrue(delete.call_args.kwargs['stream'])
        delete.return_value.close.assert_called_once()

    @patch('projects.github.requests.delete', return_value=Mock(status_code=503))
    def test_provider_failure_still_clears_locally_with_explicit_warning(self, delete):
        github.save_tokens(self.account, TOKENS)
        response = self.disconnect(True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['github_cleanup_required'])
        self.assertFalse(response.json()['github_authorization_revoked'])
        self.assertFalse(GitHubCredential.objects.exists())
        self.project.refresh_from_db(); self.assertFalse(self.project.is_active)
        self.assertTrue(SocialAccount.objects.filter(pk=self.account.pk).exists())
        github.save_tokens(self.account, TOKENS)
        response = self.delete()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['github_cleanup_required'])
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    @patch('projects.github.token_request')
    def test_expired_refresh_token_can_be_cleared(self, refresh):
        github.save_tokens(self.account, TOKENS)
        GitHubCredential.objects.update(expires_at=timezone.now() - timedelta(days=1),
                                        refresh_expires_at=timezone.now() - timedelta(days=1))
        response = self.disconnect()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['github_cleanup_required'])
        self.assertFalse(GitHubCredential.objects.exists())
        self.assertFalse(SocialAccount.objects.filter(pk=self.account.pk).exists())
        refresh.assert_not_called()

    @patch('projects.github.requests.delete', return_value=Mock(status_code=204))
    def test_account_cascade_other_user_safe_and_old_session_denied(self, delete):
        github.save_tokens(self.account, TOKENS)
        other = Client(enforce_csrf_checks=True)
        self.post('login', {'email': self.data['email'], 'password': self.data['password']}, client=other)
        stranger = User.objects.create_user(email='other@example.test', username='other', password='Safe9!xx')
        other_project = Project.objects.create(owner=stranger, repository_id=100, installation_id=11, title='Other', category='software')
        self.assertEqual(self.delete(user_id=stranger.pk).status_code, 400)
        response = self.delete()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(SocialAccount.objects.filter(pk=self.account.pk).exists())
        self.assertFalse(GitHubCredential.objects.exists())
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        self.assertFalse(SessionRecord.objects.filter(user_id=self.user.pk).exists())
        self.assertTrue(Project.objects.filter(pk=other_project.pk).exists())
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])
        self.assertIsNone(other.get('/api/auth/me/').json()['user'])
        # Same email/username can start registration again, as required for testing.
        with patch('accounts.security.reserve_verification_email', return_value=True):
            self.assertEqual(self.register().status_code, 201)

    @patch('projects.github.token_request')
    def test_pending_app_callback_invalidated(self, exchange):
        response = self.post('projects/github/start')
        state = parse_qs(urlparse(response.json()['authorization_url']).query)['state'][0]
        self.assertEqual(self.disconnect(True).status_code, 200)
        response = self.client.get('/api/auth/projects/github/callback/', {'state': state, 'code': 'test'})
        self.assertEqual(response.status_code, 403)
        exchange.assert_not_called()
        self.assertFalse(GitHubCredential.objects.exists())

    @patch('projects.github.readme', return_value='')
    @patch('projects.github.repository', return_value=('token', REPO))
    def test_inflight_create_cannot_survive_disconnect(self, repo, readme):
        # Simulate disconnect winning the User lock after provider verification.
        def disconnect_during_read(*args):
            User.objects.filter(pk=self.user.pk).update(security_version=self.user.security_version + 1)
            return ''
        readme.side_effect = disconnect_during_read
        response = self.post('projects', {'installation_id': 11, 'repository_id': 100,
                                         'title': 'Race', 'category': 'software'})
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Project.objects.filter(title='Race').exists())

    @patch('projects.github.api', side_effect=github.GitHubAccessError())
    def test_status_exposes_stored_connection_when_provider_unavailable(self, api):
        github.save_tokens(self.account, TOKENS)
        response = self.client.get('/api/auth/projects/github/status/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['credential_stored'])
        self.assertFalse(response.json()['connected'])

    @patch('projects.github.repository')
    def test_inflight_reactivation_cannot_survive_disconnect(self, repo):
        self.project.is_active = False; self.project.save()
        def disconnect_during_proof(*args):
            User.objects.filter(pk=self.user.pk).update(security_version=self.user.security_version + 1)
            return 'token', REPO
        repo.side_effect = disconnect_during_proof
        csrf = self.client.get('/api/auth/csrf/').json()['csrfToken']
        response = self.client.patch(f'/api/auth/projects/{self.project.pk}/', {'is_active': True},
                                     content_type='application/json', HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 401)
        self.project.refresh_from_db(); self.assertFalse(self.project.is_active)

    @override_settings(GITHUB_ENABLED=True, GITHUB_CLIENT_ID='test-client', GITHUB_CLIENT_SECRET='test-secret',
                       GITHUB_REDIRECT_URI='https://first.test/accounts/github/login/callback/',
                       GOOGLE_ENABLED=True, GOOGLE_CLIENT_ID='test-client', GOOGLE_CLIENT_SECRET='test-secret',
                       GOOGLE_REDIRECT_URI='https://first.test/accounts/google/login/callback/')
    def test_inflight_provider_login_invalidated_before_identity_attachment(self):
        for provider, claims in [('github', {'id': 77, 'verified_primary_email': self.user.email}),
                                 ('google', {'sub': 'new-google', 'email': self.user.email, 'email_verified': True})]:
            with self.subTest(provider=provider):
                response = self.post(provider + '/start', {'purpose': 'login'})
                self.assertEqual(response.status_code, 200, response.content)
                state = parse_qs(urlparse(response.json()['authorization_url']).query)['state'][0]
                def changed_while_exchanging(*args):
                    User.objects.filter(pk=self.user.pk).update(security_version=self.user.security_version + 1)
                    return claims
                with patch('accounts.' + provider + '_views.exchange', side_effect=changed_while_exchanging):
                    response = self.client.get('/api/auth/' + provider + '/callback/', {'state': state, 'code': 'test'})
                self.assertIn(response.status_code, (400, 401, 403))
                self.assertFalse(SocialAccount.objects.filter(user=self.user, provider='google').exists())
                # Restore only our test fixture between independent providers.
                User.objects.filter(pk=self.user.pk).update(security_version=self.user.security_version)
