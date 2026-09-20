from accounts.tests.fakes import BearerClient as Client
import base64
from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from unittest.mock import Mock, patch
from allauth.socialaccount.models import SocialAccount
from cryptography.fernet import Fernet
from django.test import TestCase, override_settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from accounts.tests import test_auth
from accounts.models import User
from . import github
from .models import Project, GitHubCredential, RepositoryCache, PreparedRepository
from .taxonomy import STAGES
import uuid

KEY = Fernet.generate_key().decode()
CONFIG = dict(GITHUB_APP_ENABLED=True, GITHUB_APP_ID='123', GITHUB_APP_SLUG='first-test', GITHUB_APP_CLIENT_ID='app-client', GITHUB_APP_CLIENT_SECRET='app-secret', GITHUB_APP_REDIRECT_URI='https://first.test/github-repo/callback', GITHUB_APP_TOKEN_KEY=KEY)
REPO = {'id': 99, 'installation_id': 11, 'full_name': 'owner/repo', 'name': 'repo', 'private': False, 'description': 'Description', 'html_url': 'https://github.com/owner/repo'}
TOKENS = {'access_token': 'sensitive-token', 'refresh_token': 'sensitive-refresh', 'token_type': 'bearer', 'expires_in': 28800, 'refresh_token_expires_in': 15000000}

@override_settings(**CONFIG)
class ProjectTests(TestCase):
    post = test_auth.AuthTests.post
    register = test_auth.AuthTests.register
    def setUp(self):
        test_auth.AuthTests.setUp(self)
        self.register()
        self.user = User.objects.get(); self.user.email_verified = True; self.user.save()
        self.account = SocialAccount.objects.create(user=self.user, provider='github', uid='77')
    def create(self, **extra):
        preview_token = uuid.uuid4()
        if SocialAccount.objects.filter(pk=self.account.pk).exists():
            credential = github.save_tokens(self.account, TOKENS)
            cache, _ = RepositoryCache.objects.get_or_create(credential=credential,
                defaults={'repositories': [getattr(self, 'repo', REPO)], 'cached_at': timezone.now()})
            PreparedRepository.objects.update_or_create(credential=credential, installation_id=11, repository_id=99,
                defaults={'preview_token': preview_token, 'cache_generation': cache.generation,
                    'repository': getattr(self, 'repo', REPO), 'readme_excerpt': 'One. Two. Three.'})
        return self.post('projects', {'installation_id': 11, 'repository_id': 99, 'preview_token': str(preview_token),
            'title': 'Projem', 'category': 'web-app', 'subcategory': 'community', 'stage': STAGES[0]['value'],
            'need_type': 'teammate', 'participation_mode': 'application', 'visibility': 'public',
            'description': 'Ekip arıyorum.', 'readme_excerpt': 'One. Two. Three.', **extra})
    def edit(self, pk, data):
        csrf = self.client.get('/api/auth/csrf/').json()['csrfToken']
        return self.client.patch(f'/api/auth/projects/{pk}/', data, content_type='application/json', HTTP_X_CSRFTOKEN=csrf)
    @patch('projects.github.readme', return_value='One. Two. Three.')
    @patch('projects.github.repository', return_value=('token', REPO))
    def test_optional_phone_duplicate_archive_and_identity_immutable(self, repo, readme):
        self.assertFalse(self.user.phone_verified); self.assertEqual(self.user.phone, '')
        response = self.create(); self.assertEqual(response.status_code, 201, response.content)
        pk=response.json()['project']['id']; self.assertEqual(self.create().status_code, 409)
        self.assertEqual(self.edit(pk, {'repository_id': 100}).status_code, 400)
        self.assertTrue(self.client.get('/api/auth/me/').json()['user']['capabilities']['can_create_listing'])
        repo.side_effect=github.GitHubAccessError()
        self.assertEqual(self.edit(pk, {'title': 'Changed'}).status_code, 200)
        repo.assert_not_called()
        self.assertEqual(self.edit(pk, {'is_active': False}).status_code, 200)
        self.post('logout'); self.assertEqual(self.client.get(f'/api/auth/projects/{pk}/').status_code, 404)
    @patch('projects.github.readme', return_value='One. Two. Three.')
    @patch('projects.github.repository', return_value=('token', {**REPO, 'private':True}))
    def test_private_and_revoked_public_serializer(self, repo, readme):
        self.repo = {**REPO, 'private': True}
        pk=self.create().json()['project']['id']; self.post('logout')
        response=self.client.get(f'/api/auth/projects/{pk}/'); data=response.json()['project']
        self.assertIsNone(data['repository_url']); self.assertIsNone(data['repository_name'])
        self.assertEqual(data['readme_excerpt'], 'One. Two. Three.')
        for secret in ['owner/repo','installation_id','repository_id','html_url','token']:
            self.assertNotIn(secret,response.content.decode())
        repo.side_effect=github.GitHubAccessError()
        self.assertEqual(self.client.get(f'/api/auth/projects/{pk}/').json()['project']['readme_excerpt'],'One. Two. Three.')
    @patch('projects.github.readme', return_value='One. Two. Three.')
    @patch('projects.github.repository', return_value=('token', REPO))
    def test_excerpt_injection_and_ownership(self, repo, readme):
        self.assertEqual(self.create(readme_excerpt='Private contents').status_code,400)
        pk=self.create(readme_excerpt='').json()['project']['id']
        self.post('logout'); self.data.update(email='other@example.com',username='Other'); self.register()
        self.assertEqual(self.edit(pk,{'is_active':False}).status_code,404)
    def test_email_link_csrf_auth_required(self):
        self.assertEqual(self.client.post('/api/auth/projects/',{},content_type='application/json').status_code,403)
        self.user.email_verified=False; self.user.save(); self.assertEqual(self.create().status_code,403)
        self.user.email_verified=True; self.user.save(); self.account.delete(); self.assertEqual(self.create().status_code,403)
        self.post('logout'); self.assertEqual(self.create().status_code,401)
    @patch('projects.github.authorized_repositories',side_effect=github.GitHubAccessError())
    def test_mine_disconnected_and_unique_database(self,repos):
        kwargs=dict(owner=self.user,repository_id=99,installation_id=11,title='Mine',category='software',readme_excerpt='Saved.')
        Project.objects.create(**kwargs)
        with self.assertRaises(IntegrityError),transaction.atomic(): Project.objects.create(**kwargs)
        Project.objects.create(**kwargs,is_active=False)
        data=self.client.get('/api/auth/projects/mine/').json()['projects']; self.assertEqual(len(data),2)
        self.assertEqual(data[0]['readme_excerpt'],'Saved.'); self.assertIsNone(data[0]['repository_url'])
    def start(self):
        response=self.post('projects/github/start'); self.assertEqual(response.status_code,200,response.content)
        params=parse_qs(urlparse(response.json()['authorization_url']).query)
        self.assertNotIn('scope',params); self.assertEqual(params['code_challenge_method'],['S256']); return params
    @patch('projects.github.api',return_value={'id':77})
    @patch('projects.github.token_request',return_value=TOKENS)
    def test_callback_encryption_pkce_replay(self,token,api):
        params=self.start(); query={'state':params['state'][0],'code':'test-code'}
        response=self.client.get('/api/auth/projects/github/callback/',query); self.assertEqual(response.status_code,200,response.content)
        stored=GitHubCredential.objects.get(); self.assertNotIn('sensitive',stored.encrypted_tokens)
        self.assertEqual(github.access_token(self.account),'sensitive-token'); self.assertIn('code_verifier',token.call_args.args[0])
        self.assertEqual(self.client.get('/api/auth/projects/github/callback/',query).status_code,403)
    @patch('projects.github.api',return_value={'id':999})
    @patch('projects.github.token_request',return_value=TOKENS)
    def test_callback_wrong_identity(self,token,api):
        params=self.start(); response=self.client.get('/api/auth/projects/github/callback/',{'state':params['state'][0],'code':'test'})
        self.assertEqual(response.status_code,403); self.assertFalse(GitHubCredential.objects.exists())
    @patch('projects.github.token_request')
    def test_callback_wrong_session(self,token):
        params=self.start(); query={'state':params['state'][0],'code':'test'}
        self.assertEqual(Client(enforce_csrf_checks=True).get('/api/auth/projects/github/callback/',query).status_code,401)
        session=self.client.session; session['github_app_binder']='wrong'; session.save()
        self.assertEqual(self.client.get('/api/auth/projects/github/callback/',query).status_code,403); token.assert_not_called()


    @patch('projects.github.authorized_repositories', return_value=('token', [REPO]))
    @patch('projects.github.api', return_value={'id':77})
    @patch('projects.github.token_request', return_value=TOKENS)
    def test_unverified_email_can_complete_repo_setup_but_not_publish(self, token, api, repos):
        self.user.email_verified = False
        self.user.save()
        params = self.start()
        response = self.client.get('/api/auth/projects/github/callback/', {'state':params['state'][0], 'code':'code'})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['return_to'], '/projelerim/yeni')
        self.assertEqual(self.client.get('/api/auth/projects/github/repositories/').json()['repositories'], [REPO])
        self.assertEqual(self.create().status_code, 403)
        self.assertEqual(self.post('projects/github/preview', {'installation_id':11, 'repository_id':99}).status_code, 403)

    @patch('projects.github.api', return_value={'id':77})
    @patch('projects.github.token_request', return_value=TOKENS)
    def test_onboarding_return_target_is_allowlisted_and_state_bound(self, token, api):
        for target in ['https://evil.test/', '//evil.test', '/hesap?next=evil', '/github-kurulum']:
            self.assertEqual(self.post('projects/github/start', {'return_to':target}).status_code, 400)
        for target in ['/', '/hesap', '/projelerim/yeni']:
            response = self.post('projects/github/start', {'return_to':target})
            self.assertEqual(response.status_code, 200)
            params = parse_qs(urlparse(response.json()['authorization_url']).query)
            rejected = self.client.get('/api/auth/projects/github/callback/', {
                'state': params['state'][0], 'code': 'code', 'return_to': 'https://evil.test/'})
            self.assertEqual(rejected.status_code, 400)
            response = self.client.get('/api/auth/projects/github/callback/', {
                'state':params['state'][0], 'code':'code'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['return_to'], target)

    @patch('projects.github.authorized_repositories')
    def test_setup_still_requires_linked_identity_session_and_csrf(self, repos):
        self.assertEqual(self.client.post('/api/auth/projects/github/start/', {}, content_type='application/json').status_code, 403)
        self.account.delete()
        self.assertEqual(self.post('projects/github/start').status_code, 403)
        self.assertEqual(self.client.get('/api/auth/projects/github/repositories/').status_code, 403)
        self.post('logout')
        self.assertEqual(self.post('projects/github/start').status_code, 401)
        self.assertEqual(self.client.get('/api/auth/projects/github/repositories/').status_code, 401)
        repos.assert_not_called()

@override_settings(**CONFIG)
class GitHubServiceTests(TestCase):
    def setUp(self):
        user=User.objects.create_user(email='user@example.com',username='user')
        self.account=SocialAccount.objects.create(user=user,provider='github',uid='77'); github.save_tokens(self.account,TOKENS)
    @patch('projects.github.token_request',return_value={**TOKENS,'access_token':'new-token','refresh_token':'new-refresh'})
    def test_refresh_rotation(self,refresh):
        GitHubCredential.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(github.access_token(self.account),'new-token'); self.assertEqual(github.access_token(self.account),'new-token'); refresh.assert_called_once()
        self.assertNotIn('new-token',GitHubCredential.objects.get().encrypted_tokens)
    @patch('projects.github.token_request')
    def test_refresh_expired(self,refresh):
        GitHubCredential.objects.update(expires_at=timezone.now()-timedelta(seconds=1),refresh_expires_at=timezone.now()-timedelta(seconds=1))
        with self.assertRaises(github.GitHubAccessError): github.access_token(self.account)
        refresh.assert_not_called()
    def responses(self,admin=True,app_id=123,uid=77):
        return [{'id':uid},{'total_count':1,'installations':[{'id':11,'app_id':app_id,'suspended_at':None}]},{'total_count':1,'repositories':[{'id':99,'full_name':'owner/repo','private':True,'permissions':{'admin':admin}}]}]
    @patch('projects.github.api')
    def test_selection_identity_app_admin_enforced(self,api):
        api.side_effect=self.responses(); self.assertEqual(github.repository(self.account,11,99)[1]['id'],99)
        for iid,rid,admin,app,uid in [(12,99,True,123,77),(11,100,True,123,77),(11,99,False,123,77),(11,99,True,999,77),(11,99,True,123,88)]:
            api.side_effect=self.responses(admin,app,uid)
            with self.assertRaises(github.GitHubAccessError): github.repository(self.account,iid,rid)
    @patch('projects.github.api',return_value={'total_count':2500,'repositories':[{}]*100})
    def test_pagination_bounded(self,api):
        with self.assertRaises(github.GitHubAccessError): github.collection('token','/fixed','repositories')
        self.assertEqual(api.call_count,20)
    def test_excerpt(self):
        value=github.excerpt('# Welcome\nHello world. [Read](https://secret.example/path) more. Third sentence! Fourth.\n![image](https://secret.example/image)\n```\nsecret code\n```\n<script>secret script</script>')
        self.assertEqual(value,'Welcome Hello world. Read more. Third sentence!'); self.assertNotIn('secret',value)
        self.assertLessEqual(len(github.excerpt('a'*1000)),600)
    @patch('projects.github.api')
    def test_readme_safe(self,api):
        api.return_value=None; self.assertEqual(github.readme('token',REPO),'')
        api.return_value={'size':300000,'encoding':'base64','content':'QQ=='}; self.assertEqual(github.readme('token',REPO),'')
        api.return_value={'size':6,'encoding':'base64','content':base64.b64encode(b'Hello.').decode()}; self.assertEqual(github.readme('token',REPO),'Hello.')
    @patch('projects.github.requests.post')
    def test_nonexpiring_rejected(self,post):
        post.return_value=Mock(status_code=200); post.return_value.json.return_value={'access_token':'a','token_type':'bearer'}
        with self.assertRaises(github.GitHubAccessError): github.token_request({'code':'code'})

    @patch('projects.github.requests.get')
    def test_http_download_bounded_and_no_redirects(self,get):
        response=Mock(status_code=200)
        response.iter_content.return_value=iter([b'x'*1_000_001,b'x'*1_000_001])
        get.return_value=response
        with self.assertRaises(github.GitHubAccessError): github.api('token','/user')
        self.assertFalse(get.call_args.kwargs['allow_redirects']); self.assertTrue(get.call_args.kwargs['stream'])
        response.close.assert_called_once()

    @patch('projects.github.requests.get')
    def test_malformed_json_provider_safe(self,get):
        response=Mock(status_code=200); response.iter_content.return_value=iter([b'[]']); get.return_value=response
        with self.assertRaises(github.GitHubAccessError): github.api('token','/user')

    @patch('projects.github.requests.post')
    def test_malformed_token_type_safe(self,post):
        post.return_value=Mock(status_code=200); post.return_value.json.return_value={**TOKENS,'token_type':None}
        with self.assertRaises(github.GitHubAccessError): github.token_request({'code':'code'})

    def test_html_entities_unclosed_code_and_indented_code_removed(self):
        value=github.excerpt('Hello. &lt;script&gt;secret&lt;/script&gt; World.\n    secret code\n```secret unclosed')
        self.assertEqual(value,'Hello. World.')

    @patch('projects.github.api')
    def test_malformed_repo_permissions_fail_closed(self,api):
        data=self.responses(); data[-1]['repositories'][0]['permissions']=None; api.side_effect=data
        with self.assertRaises(github.GitHubAccessError): github.repository(self.account,11,99)

    @patch('projects.github.time.monotonic', side_effect=[0, 6])
    @patch('projects.github.requests.get')
    def test_stream_without_outer_budget_has_deadline(self,get,clock):
        response=Mock(status_code=200); response.iter_content.return_value=iter([b'{}']); get.return_value=response
        with self.assertRaises(github.GitHubAccessError): github.api('token','/user')
        response.close.assert_called_once()
