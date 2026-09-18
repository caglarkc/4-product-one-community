from io import StringIO
from unittest.mock import Mock, patch
from django.core.management import call_command
from django.test import TestCase
from allauth.socialaccount.models import SocialAccount
from accounts.connected_accounts import provider_metadata, sanitize_metadata
from accounts.serializers import user_data
from accounts.models import User


class ConnectedAccountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='first_user', email='first@example.com')

    def test_only_own_whitelisted_provider_fields_and_legacy_fallback(self):
        SocialAccount.objects.create(user=self.user, provider='google', uid='g', extra_data={})
        other = User.objects.create_user(username='other', email='other@example.com')
        SocialAccount.objects.create(user=other, provider='github', uid='2', extra_data={'email': 'private@example.com'})
        data = user_data(self.user)
        self.assertEqual(data['providers'], ['google'])
        self.assertEqual(data['connected_accounts'], [{'provider': 'google', 'display_name': '', 'username': '',
            'email': '', 'avatar_url': '', 'profile_url': ''}])

    def test_metadata_whitelist_and_canonical_github_profile(self):
        result = provider_metadata('github', {'login': 'my-name', 'name': 'Name', 'id': 1,
            'email': 'unverified@example.com', 'verified_primary_email': 'verified@example.com',
            'avatar_url': 'https://avatars.githubusercontent.com/u/1?v=4', 'html_url': 'javascript:bad',
            'access_token': 'secret', 'private_repos': 123})
        self.assertEqual(result, {'display_name': 'Name', 'username': 'my-name', 'email': 'verified@example.com',
            'avatar_url': 'https://avatars.githubusercontent.com/u/1?v=4', 'profile_url': 'https://github.com/my-name'})
        for url in ['javascript:bad', 'http://avatars.githubusercontent.com/u/1',
                    'https://avatars.githubusercontent.com.evil.test/u/1',
                    'https://user@avatars.githubusercontent.com/u/1', 'https://avatars.githubusercontent.com:444/u/1']:
            self.assertEqual(sanitize_metadata('github', {'avatar_url': url})['avatar_url'], '')
        self.assertEqual(sanitize_metadata('github', {'username': '../bad'})['profile_url'], '')

    def test_backfill_dry_run_then_persists_no_email_or_identity_change(self):
        account = SocialAccount.objects.create(user=self.user, provider='github', uid='123')
        response = Mock(status_code=200)
        response.json.return_value = {'id': 123, 'login': 'real-login', 'name': 'Public', 'email': 'public@example.com',
                                     'avatar_url': 'https://avatars.githubusercontent.com/u/123'}
        with patch('accounts.management.commands.backfill_github_profiles.requests.get', return_value=response) as get:
            call_command('backfill_github_profiles', dry_run=True, stdout=StringIO())
            account.refresh_from_db(); self.assertEqual(account.extra_data, {})
            output = StringIO(); call_command('backfill_github_profiles', stdout=output)
            self.assertIn('updated=1', output.getvalue())
            self.assertFalse(get.call_args.kwargs['allow_redirects'])
            self.assertEqual(get.call_args.args[0], 'https://api.github.com/user/123')
        account.refresh_from_db()
        self.assertEqual(account.extra_data['username'], 'real-login')
        self.assertEqual(account.extra_data['email'], '')
        self.assertEqual(account.uid, '123'); self.assertEqual(account.user_id, self.user.pk)

    def test_backfill_rejects_wrong_id_and_preserves_concurrent_metadata(self):
        account = SocialAccount.objects.create(user=self.user, provider='github', uid='123')
        response = Mock(status_code=200); response.json.return_value = {'id': 124, 'login': 'wrong'}
        with patch('accounts.management.commands.backfill_github_profiles.requests.get', return_value=response):
            call_command('backfill_github_profiles', stdout=StringIO())
        account.refresh_from_db(); self.assertEqual(account.extra_data, {})
        def concurrent(*args, **kwargs):
            account.extra_data = provider_metadata('github', {'login': 'new-login', 'name': 'New',
                'verified_primary_email': 'new@example.com', 'avatar_url': 'https://avatars.githubusercontent.com/u/123'})
            account.save()
            response.json.return_value = {'id': 123, 'login': 'old-login', 'name': 'Old'}
            return response
        with patch('accounts.management.commands.backfill_github_profiles.requests.get', side_effect=concurrent):
            call_command('backfill_github_profiles', stdout=StringIO())
        account.refresh_from_db()
        self.assertEqual(account.extra_data['username'], 'new-login')
        self.assertEqual(account.extra_data['email'], 'new@example.com')
