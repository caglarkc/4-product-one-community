"""Provider security regressions; no database, network or GitHub mutations."""
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock, patch
from django.test import SimpleTestCase
from . import github_participation as p
from .github import GitHubAccessError


class ProviderTests(SimpleTestCase):
    def setUp(self):
        self.owner = SimpleNamespace(uid='11', provider='github')
        self.reader = SimpleNamespace(uid='22', provider='github')
        self.project = SimpleNamespace(repository_id=123, installation_id=7, is_private=False)
        self.repo = {'id': 123, 'full_name': 'owner/repo', 'private': False, 'permissions': {'admin': True},
                     'default_branch': 'main', 'owner': {'id': 11, 'type': 'User', 'login': 'owner'}}
        self.path = '/repos/owner/repo'
        self.pr = {'id': 60, 'number': 3, 'title': 'Fix', 'base': {'repo': {'id': 123}},
                   'head': {'sha': 'a'*40}, 'user': {'id': 22}, 'state': 'open', 'draft': False}
        guard = patch.object(p.requests, 'request', side_effect=AssertionError('Unexpected network'))
        guard.start()
        self.addCleanup(guard.stop)

    def owner_context(self, repo=None):
        return patch.object(p, '_owner', return_value=('owner-token', self.path, repo or self.repo))

    def failure(self, code, fn, *args, **kwargs):
        with self.assertRaises(GitHubAccessError) as exc:
            fn(*args, **kwargs)
        self.assertEqual(str(exc.exception.detail['code']), code)

    def rules(self):
        branch = {'id': 1, 'target': 'branch', 'enforcement': 'active',
                  'bypass_actors': [{'actor_type': 'RepositoryRole', 'actor_id': 5}],
                  'conditions': {'ref_name': {'include': ['~ALL'], 'exclude': []}},
                  'rules': [{'type': 'update', 'parameters': {'update_allows_fetch_and_merge': False}},
                            {'type': 'deletion'}, {'type': 'non_fast_forward'}]}
        tag = deepcopy(branch)
        tag.update(id=2, target='tag')
        return [branch, tag]

    def safety(self, rules=None, repo=None, plan=None):
        rules = self.rules() if rules is None else rules
        def listing(token, path, params=None):
            return [{'id': r['id']} for r in rules] if path.endswith('/rulesets') else [{'name':'main'}, {'name':'release'}]
        def api(token, path, **kwargs):
            if path == '/user' or path.startswith('/orgs/'):
                return plan or {'id': 11}
            return next(r for r in rules if path.endswith('/'+str(r['id'])))
        with self.owner_context(repo), patch.object(p, '_list', side_effect=listing), patch.object(p, '_api', side_effect=api):
            return p.automatic_access_safety(self.owner, self.project)

    def test_auto_requires_all_existing_branches_and_all_tags(self):
        self.assertEqual(self.safety()['protected_branch_count'], 2)
        rules = self.rules()
        rules[0]['conditions']['ref_name']['include'] = ['~DEFAULT_BRANCH']
        self.failure('github_protection_required', self.safety, rules=rules)
        self.failure('github_protection_required', self.safety, rules=self.rules()[:1])

    def test_auto_rejects_untrusted_bypass_actors(self):
        for actor in [{'actor_type':'RepositoryRole','actor_id':4}, {'actor_type':'User','actor_id':22},
                      {'actor_type':'Integration','actor_id':7}, {'actor_type':'Team','actor_id':8}]:
            with self.subTest(actor=actor):
                rules = self.rules()
                rules[0]['bypass_actors'] = [actor]
                self.failure('github_protection_required', self.safety, rules=rules)

    def test_auto_rejects_weakened_or_unprovable_rules(self):
        for case in ['evaluate', 'missing_bypass', 'fetch_merge', 'no_delete', 'exclude', 'wildcard']:
            with self.subTest(case=case):
                rules = self.rules()
                if case == 'evaluate': rules[0]['enforcement'] = 'evaluate'
                elif case == 'missing_bypass': rules[0].pop('bypass_actors')
                elif case == 'fetch_merge': rules[0]['rules'][0]['parameters']['update_allows_fetch_and_merge'] = True
                elif case == 'no_delete': rules[0]['rules'].pop(1)
                elif case == 'exclude': rules[0]['conditions']['ref_name']['exclude'] = ['refs/heads/release']
                else: rules[0]['conditions']['ref_name']['include'] = ['refs/heads/*']
                self.failure('github_protection_required', self.safety, rules=rules)

    def test_private_plan_fails_closed(self):
        repo = {**self.repo, 'private':True}
        for plan in [{'id':11}, {'id':11,'plan':{'name':'free'}}, {'id':99,'plan':{'name':'pro'}}]:
            with self.subTest(plan=plan): self.failure('github_protection_required', self.safety, repo=repo, plan=plan)
        self.assertTrue(self.safety(repo=repo, plan={'id':11,'plan':{'name':'pro'}})['safe'])
        repo['owner'] = {'id':50,'login':'org','type':'Organization'}
        self.failure('github_protection_required', self.safety, repo=repo, plan={'plan':{'name':'free'}})
        self.assertTrue(self.safety(repo=repo, plan={'plan':{'name':'team'}})['safe'])

    def test_owner_pins_numeric_repository_and_current_admin(self):
        with patch.object(p.github,'access_token',return_value='app'), patch.object(p,'_api',side_effect=[{'id':11},self.repo]) as api, p.operation_budget():
            self.assertEqual(p._owner(self.owner,self.project)[1],self.path)
            self.assertEqual(api.call_args.args,('app','/repositories/123'))
        for change in [{'id':124}, {'permissions':{'admin':False}}, {'full_name':'../bad?token=x'}, {'archived':True}]:
            with self.subTest(change=change), patch.object(p.github,'access_token',return_value='app'), patch.object(p,'_api',side_effect=[{'id':11},{**self.repo,**change}]), p.operation_budget():
                self.failure('repository_not_authorized',p._owner,self.owner,self.project)

    def test_owner_token_identity_mismatch_stops_early(self):
        with patch.object(p.github,'access_token',return_value='app'), patch.object(p,'_api',return_value={'id':99}) as api, p.operation_budget():
            self.failure('github_identity_mismatch',p._owner,self.owner,self.project)
            self.assertEqual(api.call_count,1)

    def test_public_content_never_borrows_owner_token(self):
        with self.owner_context(), patch.object(p,'_list',return_value=[self.pr]) as listing:
            p.pull_requests(self.owner,self.project,self.reader)
            self.assertIsNone(listing.call_args.args[0])

    def test_stored_public_now_private_content_uses_reader_token(self):
        with self.owner_context({**self.repo,'private':True}), patch.object(p.github,'access_token',return_value='reader'), patch.object(p,'_api',return_value={'id':22}), patch.object(p,'_list',return_value=[self.pr]) as listing:
            p.pull_requests(self.owner,self.project,self.reader)
            self.assertEqual(listing.call_args.args[0],'reader')
        with self.owner_context({**self.repo,'private':True}), patch.object(p,'_list') as listing:
            self.failure('github_repository_read_required',p.pull_requests,self.owner,self.project)
            listing.assert_not_called()

    def test_private_wrong_reader_identity_never_fetches_content(self):
        with self.owner_context({**self.repo,'private':True}), patch.object(p.github,'access_token',return_value='reader'), patch.object(p,'_api',return_value={'id':99}), patch.object(p,'_list') as listing:
            self.failure('github_identity_mismatch',p.pull_requests,self.owner,self.project,self.reader)
            listing.assert_not_called()

    def test_pr_submission_rejects_private_wrong_author_repo_and_states(self):
        with self.owner_context({**self.repo,'private':True}), patch.object(p,'_api') as api:
            self.failure('github_public_pull_required',p.check_pull_request,self.owner,self.project,3,self.reader)
            api.assert_not_called()
        for change,code in [({'user':{'id':99}},'github_pull_author_mismatch'), ({'base':{'repo':{'id':999}}},'github_pull_repository_mismatch'), ({'state':'closed'},'github_pull_not_open'), ({'draft':True},'github_pull_not_open'), ({'merged':True},'github_pull_not_open')]:
            with self.subTest(change=change), self.owner_context(), patch.object(p,'_api',return_value={**self.pr,**change}):
                self.failure(code,p.check_pull_request,self.owner,self.project,3,self.reader)

    def test_merge_changed_sha_never_writes_success_pins_sha(self):
        with self.owner_context(), patch.object(p,'_api',return_value=self.pr) as api:
            self.failure('github_pull_changed',p.merge_pull_request,self.owner,self.project,3,self.reader,'b'*40)
            self.assertEqual(api.call_count,1)
        with self.owner_context(), patch.object(p,'_api',side_effect=[self.pr,{'merged':True}]) as api:
            self.assertTrue(p.merge_pull_request(self.owner,self.project,3,self.reader,'a'*40)['merged'])
            self.assertEqual(api.call_args.kwargs['data']['sha'],'a'*40)
            self.assertEqual(api.call_args.kwargs['method'],'PUT')

    def test_already_merged_retry_is_read_only(self):
        with self.owner_context(), patch.object(p,'_api',return_value={**self.pr,'merged':True,'state':'closed'}) as api:
            self.assertTrue(p.merge_pull_request(self.owner,self.project,3,self.reader,'a'*40)['merged'])
            self.assertEqual(api.call_count,1)

    def test_issue_retry_reconciles_marker_and_relink_never_duplicates(self):
        row = {'id':10,'number':2,'title':'Need','state':'open','body':'<!-- FIRST issue operation: op-1 -->','user':{'id':11}}
        with self.owner_context(), patch.object(p,'_list',return_value=[row]), patch.object(p,'_api') as api:
            self.assertEqual(p.create_issue(self.owner,self.project,'Need','Body','op-1')['number'],2)
            api.assert_not_called()
        with self.owner_context(), patch.object(p,'_list',return_value=[{**row,'user':{'id':99}}]), patch.object(p,'_api') as api:
            self.failure('github_issue_operation_identity_changed',p.create_issue,self.owner,self.project,'Need','Body','op-1')
            api.assert_not_called()

    def test_read_invitation_never_counts_as_write(self):
        for permission,expected in [('read','missing'),('write','invited')]:
            with self.subTest(permission=permission), patch.object(p,'_api',return_value=None), patch.object(p,'_list',return_value=[{'id':5,'invitee':{'id':22},'permissions':permission}]), p.operation_budget():
                self.assertEqual(p._invitation_status('t',self.path,self.repo,{'id':22,'login':'reader'})['status'],expected)

    def test_existing_admin_reported_without_rewriting_permissions(self):
        with self.owner_context(), patch.object(p,'_target',return_value={'id':22,'login':'reader'}), patch.object(p,'_api',return_value={'user':{'id':22},'permission':'admin','role_name':'admin'}) as api:
            result = p.invite_collaborator(self.owner,self.project,self.reader)
            self.assertEqual(result['access_level'],'admin')
            self.assertTrue(result['existing_access'])
            self.assertEqual(api.call_count,1)
            self.assertNotIn('method',api.call_args.kwargs)

    def test_target_username_identity_race_is_rejected(self):
        with patch.object(p,'_api',side_effect=[{'id':22,'login':'reader'},{'id':99,'login':'reader'}]), p.operation_budget():
            self.failure('github_identity_mismatch',p._target,'t',self.reader)

    def test_redirects_are_not_followed_and_response_closed(self):
        response = Mock(status_code=302)
        with patch.object(p.requests,'request',return_value=response) as request, p.operation_budget():
            self.failure('github_permission_or_operation_failed',p._api,'secret','/user')
            self.assertFalse(request.call_args.kwargs['allow_redirects'])
            self.assertEqual(request.call_args.args[1],'https://api.github.com/user')
            response.close.assert_called_once()

    def test_anonymous_transport_omits_authorization(self):
        response = Mock(status_code=200)
        response.iter_content.return_value = [b'[]']
        with patch.object(p.requests,'request',return_value=response) as request, p.operation_budget():
            self.assertEqual(p._api(None,'/repos/owner/repo/pulls'),[])
            self.assertNotIn('Authorization',request.call_args.kwargs['headers'])

    def test_nested_budget_cannot_reset_deadline(self):
        with patch.object(p.time,'monotonic',return_value=100), p.operation_budget():
            outer = p._budget.get()
            with p.operation_budget():
                self.assertIs(p._budget.get(),outer)
                with patch.object(p.time,'monotonic',return_value=121):
                    self.failure('github_request_limit',p._api,'t','/user')
        self.assertIsNone(p._budget.get())

    def test_oversized_and_trickling_response_closed(self):
        response = Mock(status_code=200)
        response.iter_content.return_value = [b'x'*2_000_001]
        with patch.object(p.requests,'request',return_value=response), p.operation_budget():
            self.failure('github_response_limit',p._api,'t','/user')
            response.close.assert_called_once()
        response = Mock(status_code=200)
        response.iter_content.return_value = [b'{']
        with patch.object(p.requests,'request',return_value=response), patch.object(p.time,'monotonic',side_effect=[100,100,121]), p.operation_budget():
            self.failure('github_response_limit',p._api,'t','/user')
            response.close.assert_called_once()

    def test_incomplete_pagination_fails_closed(self):
        with patch.object(p,'_api',return_value=[{'id':n} for n in range(100)]) as api, p.operation_budget():
            self.failure('github_collection_limit',p._list,'t','/repos/owner/repo/invitations')
            self.assertEqual(api.call_count,10)
