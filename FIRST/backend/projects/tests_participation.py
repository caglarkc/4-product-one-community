"""Participation API integration tests using real sessions/CSRF and isolated providers."""
from unittest.mock import patch
from django.test import TestCase, override_settings
from allauth.socialaccount.models import SocialAccount
from accounts.models import User, SessionRecord
from accounts.tests import test_auth
from accounts.tests.fakes import BearerClient
from .models import Project, Participation, ProjectViewer, Notification
from .tests import CONFIG, ProjectTests
from .taxonomy import STAGES
from .github import GitHubAccessError

PROVIDER = 'projects.github_participation.'
INVITE = {'status': 'invited', 'invitation_id': 41, 'url': 'https://github.com/owner/repo/invitations'}
PR = {'id': 2, 'number': 7, 'sha': 'a' * 40, 'state': 'open', 'merged': False, 'draft': False,
      'url': 'https://github.com/owner/repo/pull/7', 'title': 'Change'}


@override_settings(**CONFIG)
class ParticipationTests(TestCase):
    post = test_auth.AuthTests.post
    register = test_auth.AuthTests.register
    create = ProjectTests.create

    def setUp(self):
        test_auth.AuthTests.setUp(self)
        self.register()
        self.user = User.objects.get()
        self.user.email_verified = True
        self.user.save()
        self.account = SocialAccount.objects.create(user=self.user, provider='github', uid='77')
        self.candidate = User.objects.create_user(email='candidate@example.com', username='Candidate',
            password='Test-password9!', email_verified=True)
        self.candidate_account = SocialAccount.objects.create(user=self.candidate, provider='github', uid='88')
        self.candidate_client = BearerClient(enforce_csrf_checks=True)
        self.assertEqual(self.post('login', {'email': self.candidate.email, 'password': 'Test-password9!'},
                                  client=self.candidate_client).status_code, 200)
        self.project = Project.objects.create(owner=self.user, repository_id=500, installation_id=11,
            repository_name='owner/repo', repository_url='https://github.com/owner/repo',
            is_private=False, title='Test project', category='web-app', subcategory='community',
            stage=STAGES[0]['value'], need_type='teammate', participation_mode='application',
            visibility='public', applications_open=True)

    def update_project(self, **values):
        for key, value in values.items():
            setattr(self.project, key, value)
        self.project.save()

    def apply(self, **data):
        return self.post(f'projects/{self.project.pk}/apply', {'explanation': 'I can contribute.', **data},
                         client=self.candidate_client)

    def action(self, row, action, client=None, **extra):
        return self.post(f'projects/participation/{row.pk}/action', {'action': action, **extra}, client=client)

    def listing_patch(self, **data):
        csrf = self.client.get('/api/auth/csrf/').json()['csrfToken']
        return self.client.patch(f'/api/auth/projects/{self.project.pk}/', data,
                                content_type='application/json', HTTP_X_CSRFTOKEN=csrf)

    def test_real_bearer_cookie_is_not_auth_and_csrf_is_required(self):
        self.assertTrue(self.candidate_client.defaults['HTTP_AUTHORIZATION'].startswith('Bearer '))
        result = self.candidate_client.post(f'/api/auth/projects/{self.project.pk}/apply/',
            {'explanation': 'hello'}, content_type='application/json')
        self.assertEqual(result.status_code, 403)
        stranger = BearerClient(enforce_csrf_checks=True)
        stranger.cookies['sessionid'] = self.candidate_client.session.session_key
        self.assertEqual(self.post(f'projects/{self.project.pk}/apply', {'explanation': 'hello'}, client=stranger).status_code, 401)
        self.assertFalse(Participation.objects.exists())

    def test_application_explanation_email_and_github_required(self):
        self.assertEqual(self.apply(explanation='').status_code, 400)
        self.candidate.email_verified = False; self.candidate.save()
        self.assertEqual(self.apply().status_code, 403)
        self.candidate.email_verified = True; self.candidate.save()
        self.candidate_account.delete()
        self.assertEqual(self.apply().status_code, 403)
        self.assertFalse(Participation.objects.exists())

    def test_apply_duplicate_and_withdraw(self):
        self.assertEqual(self.apply().status_code, 201)
        self.assertEqual(self.apply().status_code, 200)
        self.assertEqual(Participation.objects.count(), 1)
        row = Participation.objects.get()
        self.assertEqual(row.github_uid, '88')
        self.assertEqual(self.action(row, 'withdraw', self.candidate_client).status_code, 200)
        row.refresh_from_db(); self.assertEqual(row.status, 'withdrawn')
        self.assertEqual(self.action(row, 'accept').status_code, 409)

    @patch(PROVIDER + 'invite_collaborator', return_value=INVITE)
    def test_accept_after_close_is_idempotent_and_not_membership(self, invite):
        self.apply(); row = Participation.objects.get()
        self.assertEqual(self.listing_patch(applications_open=False).status_code, 200)
        self.project.refresh_from_db(); self.assertEqual(self.project.visibility, 'link')
        response = self.action(row, 'accept')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['participation']['github_status'], 'invited')
        self.assertEqual(self.action(row, 'accept').status_code, 200)
        invite.assert_called_once()
        self.assertEqual(Notification.objects.filter(kind='participation_accepted').count(), 1)

    @patch(PROVIDER + 'invite_collaborator')
    def test_reject_has_no_github_effect(self, invite):
        self.apply(); row = Participation.objects.get()
        self.assertEqual(self.action(row, 'reject').status_code, 200)
        self.assertEqual(self.action(row, 'accept').status_code, 409)
        invite.assert_not_called()

    def test_closed_selected_archived_and_owner_cannot_apply(self):
        for change in [{'applications_open': False}, {'applications_open': True, 'visibility': 'selected'},
                       {'visibility': 'public', 'is_active': False}]:
            self.update_project(**change)
            self.assertIn(self.apply().status_code, [403, 404])
        self.update_project(is_active=True, visibility='public')
        self.assertEqual(self.post(f'projects/{self.project.pk}/apply', {'explanation': 'self'}).status_code, 403)
        self.assertFalse(Participation.objects.exists())

    def test_selected_viewer_is_not_participation_permission(self):
        self.update_project(visibility='selected')
        path = f'/api/auth/projects/{self.project.pk}/'
        self.assertEqual(self.candidate_client.get(path).status_code, 404)
        response = self.post(f'projects/{self.project.pk}/viewers', {'username': 'candidate'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.candidate_client.get(path).status_code, 200)
        self.assertEqual(self.apply().status_code, 403)
        self.assertFalse(Participation.objects.exists())

    @patch(PROVIDER + 'invite_collaborator', return_value=INVITE)
    def test_private_selected_invitation_visibility_and_recipient_accept(self, invite):
        self.update_project(is_private=True, visibility='selected')
        response = self.post(f'projects/{self.project.pk}/invitations', {'username': 'Candidate'})
        self.assertEqual(response.status_code, 201)
        row = Participation.objects.get()
        invite.assert_not_called()
        self.assertEqual(self.candidate_client.get(f'/api/auth/projects/{self.project.pk}/').status_code, 200)
        self.assertFalse(ProjectViewer.objects.exists())
        self.assertEqual(self.action(row, 'accept').status_code, 403)
        self.assertEqual(self.action(row, 'accept', self.candidate_client).status_code, 200)
        invite.assert_called_once()

    def test_invitation_converts_idle_previous_application_and_preserves_context(self):
        self.apply(); row = Participation.objects.get()
        self.action(row, 'withdraw', self.candidate_client)
        self.update_project(visibility='selected')
        response = self.post(f'projects/{self.project.pk}/invitations', {'username': 'Candidate'})
        self.assertEqual(response.status_code, 201)
        row.refresh_from_db()
        self.assertEqual((row.kind, row.status), ('invitation', 'invited'))
        self.assertEqual(row.explanation, 'I can contribute.')
        self.assertEqual(self.candidate_client.get(f'/api/auth/projects/{self.project.pk}/').status_code, 200)
        self.assertEqual(self.post(f'projects/{self.project.pk}/invitations', {'username': 'Candidate'}).status_code, 200)
        self.assertEqual(Notification.objects.filter(kind='participation_invitation').count(), 1)

    def test_invitation_cannot_overwrite_uncertain_operation(self):
        self.apply(); row = Participation.objects.get()
        row.operation_state = 'failed'; row.decision = 'accept'; row.save()
        self.assertEqual(self.post(f'projects/{self.project.pk}/invitations', {'username': 'Candidate'}).status_code, 409)
        row.refresh_from_db(); self.assertEqual(row.kind, 'application')

    @patch(PROVIDER + 'invite_collaborator', side_effect=GitHubAccessError({'code': 'github_protection_required'}))
    def test_automatic_failed_safety_persists_retry_and_no_success(self, invite):
        self.update_project(participation_mode='automatic')
        self.assertEqual(self.apply().status_code, 503)
        row = Participation.objects.get()
        self.assertEqual((row.status, row.operation_state), ('pending', 'failed'))
        self.assertTrue(invite.call_args.kwargs['automatic'])
        self.assertFalse(Notification.objects.filter(kind='participation_accepted').exists())
        self.assertEqual(self.action(row, 'withdraw', self.candidate_client).status_code, 409)
        invite.side_effect = None; invite.return_value = INVITE
        self.assertEqual(self.action(row, 'accept', self.candidate_client).status_code, 200)

    @patch(PROVIDER + 'automatic_access_safety', side_effect=GitHubAccessError())
    def test_automatic_create_is_fail_closed(self, safety):
        response = self.create(participation_mode='automatic')
        self.assertEqual(response.status_code, 503)
        self.assertFalse(Project.objects.filter(repository_id=99).exists())

    @patch(PROVIDER + 'invite_collaborator', return_value=INVITE)
    def test_relinked_candidate_identity_never_receives_old_acceptance(self, invite):
        self.apply(); row = Participation.objects.get()
        self.candidate_account.uid = '999'; self.candidate_account.save()
        self.assertEqual(self.action(row, 'accept').status_code, 403)
        invite.assert_not_called()
        row.refresh_from_db(); self.assertEqual(row.github_uid, '88')

    @patch(PROVIDER + 'invite_collaborator')
    @patch(PROVIDER + 'merge_pull_request', return_value={**PR, 'merged': True})
    @patch(PROVIDER + 'check_pull_request', return_value=PR)
    def test_pr_merge_then_failed_invite_reconciles_same_decision(self, check, merge, invite):
        self.update_project(participation_mode='pr')
        self.assertEqual(self.apply(pr_number=7).status_code, 201)
        row = Participation.objects.get()
        invite.side_effect = GitHubAccessError()
        self.assertEqual(self.action(row, 'accept_and_invite', expected_sha=PR['sha']).status_code, 503)
        row.refresh_from_db(); self.assertTrue(row.merged)
        self.assertEqual(self.action(row, 'accept', expected_sha=PR['sha']).status_code, 409)
        invite.side_effect = None; invite.return_value = INVITE
        self.assertEqual(self.action(row, 'accept_and_invite', expected_sha=PR['sha']).status_code, 200)
        self.assertEqual(Notification.objects.filter(kind='participation_accepted').count(), 1)

    @patch(PROVIDER + 'merge_pull_request')
    @patch(PROVIDER + 'check_pull_request', return_value=PR)
    def test_stale_review_sha_releases_only_proven_preflight_failure(self, check, merge):
        self.update_project(participation_mode='pr'); self.apply(pr_number=7)
        row = Participation.objects.get()
        merge.side_effect = GitHubAccessError({'code': 'github_pull_changed'})
        self.assertEqual(self.action(row, 'accept', expected_sha=PR['sha']).status_code, 409)
        row.refresh_from_db(); self.assertEqual((row.operation_state, row.decision), ('idle', ''))
        merge.side_effect = None; merge.return_value = {**PR, 'sha': 'b' * 40, 'merged': True}
        self.assertEqual(self.action(row, 'accept', expected_sha='b' * 40).status_code, 200)
        row.refresh_from_db(); self.assertEqual(row.pr_sha, 'b' * 40)

    @patch(PROVIDER + 'check_pull_request', side_effect=GitHubAccessError())
    def test_wrong_or_unavailable_pr_does_not_persist_application(self, check):
        self.update_project(participation_mode='pr')
        self.assertEqual(self.apply(pr_number=7).status_code, 503)
        self.assertFalse(Participation.objects.exists())

    def test_private_pr_listing_and_mutating_method_rejected(self):
        self.repo = {'id': 99, 'installation_id': 11, 'full_name': 'owner/private', 'private': True,
                     'html_url': 'https://github.com/owner/private'}
        self.assertEqual(self.create(participation_mode='pr').status_code, 400)
        self.assertEqual(self.listing_patch(participation_mode='automatic').status_code, 400)
        self.assertEqual(self.listing_patch(need_type='bug').status_code, 400)

    @patch(PROVIDER + 'pull_requests', side_effect=GitHubAccessError({'code': 'github_repository_read_required'}))
    def test_private_collaboration_requires_live_reader_not_listing_visibility(self, pulls):
        self.update_project(is_private=True, issue_number=9, issue_status='ready')
        result = self.post(f'projects/{self.project.pk}/collaboration', client=self.candidate_client)
        self.assertEqual(result.status_code, 503)
        self.assertEqual(pulls.call_args.kwargs['reader_account'].uid, '88')
        detail = self.candidate_client.get(f'/api/auth/projects/{self.project.pk}/').json()['project']
        self.assertIsNone(detail['repository_url']); self.assertIsNone(detail['issue_number'])

    @patch(PROVIDER + 'create_issue', side_effect=GitHubAccessError())
    def test_issue_create_failure_persists_hidden_retryable_listing_and_uid(self, create_issue):
        response = self.create(need_type='feature', current_state='Today', desired_outcome='Tomorrow', create_issue=True)
        self.assertEqual(response.status_code, 201)
        project = Project.objects.get(repository_id=99)
        self.assertEqual((project.issue_status, project.issue_creator_uid), ('failed', '77'))
        self.assertNotIn(str(project.pk), [p['id'] for p in self.client.get('/api/auth/projects/').json()['projects']])
        self.account.uid = '999'; self.account.save()
        count = create_issue.call_count
        self.assertEqual(self.post(f'projects/{project.pk}/issue').status_code, 503)
        self.assertEqual(create_issue.call_count, count)
        self.account.uid = '77'; self.account.save()
        create_issue.side_effect = None; create_issue.return_value = {'number': 12}
        self.assertEqual(self.post(f'projects/{project.pk}/issue').status_code, 200)
        project.refresh_from_db(); self.assertEqual(project.issue_number, 12)

    @patch(PROVIDER + 'issue', return_value={'number': 12})
    def test_existing_issue_validated_and_feature_fields_required(self, issue):
        self.assertEqual(self.create(need_type='bug').status_code, 400)
        response = self.create(need_type='bug', current_state='Broken', desired_outcome='Fixed', issue_number=12)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['project']['issue_status'], 'ready')
        self.assertEqual(issue.call_args.kwargs['reader_account'].uid, '77')

    def test_feed_filters_strict_summary_and_ordinary_reads_never_call_provider(self):
        self.update_project(current_state='sensitive long text')
        with patch(PROVIDER + 'pull_requests') as pulls, patch(PROVIDER + 'issue') as issue:
            response = self.client.get('/api/auth/projects/?need_type=teammate&participation_mode=application')
            self.assertEqual(response.json()['count'], 1)
            summary = response.json()['projects'][0]
            for field in ['owner_username', 'current_state', 'desired_outcome', 'issue_number', 'repository_id']:
                self.assertNotIn(field, summary)
            self.client.get(f'/api/auth/projects/{self.project.pk}/')
            self.client.get('/api/auth/projects/mine/')
            pulls.assert_not_called(); issue.assert_not_called()
        self.assertEqual(self.client.get('/api/auth/projects/?need_type=bug').json()['count'], 0)
        self.assertEqual(self.client.get('/api/auth/projects/?need_type=unknown').status_code, 400)

    def test_notifications_owner_scope(self):
        self.apply()
        notification = Notification.objects.get()
        self.assertEqual(self.post(f'projects/notifications/{notification.pk}/read', client=self.candidate_client).status_code, 404)
        self.assertEqual(self.post(f'projects/notifications/{notification.pk}/read').status_code, 200)
        notification.refresh_from_db(); self.assertTrue(notification.is_read)

    @patch(PROVIDER + 'invitation_status', return_value={'status': 'active', 'invitation_id': None, 'url': None})
    @patch(PROVIDER + 'invite_collaborator', return_value=INVITE)
    def test_explicit_invitation_refresh_distinguishes_active(self, invite, status):
        self.apply(); row = Participation.objects.get(); self.action(row, 'accept')
        response = self.action(row, 'refresh', self.candidate_client)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['participation']['github_status'], 'active')

    @patch(PROVIDER + 'pull_requests', return_value=[])
    def test_action_rate_limit_precedes_provider_work(self, pulls):
        from accounts import security
        for _ in range(15):
            security.count('participation-actions', str(self.candidate.pk), ttl=60)
        self.assertEqual(self.post(f'projects/{self.project.pk}/collaboration', client=self.candidate_client).status_code, 429)
        pulls.assert_not_called()
