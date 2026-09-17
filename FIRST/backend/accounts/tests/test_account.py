import time
from urllib.parse import urlparse, parse_qs
from unittest.mock import patch
from django.core import mail
from django.test import Client, TestCase
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, SessionRecord
from accounts import security
from . import test_auth


class AccountTests(TestCase):
    post = test_auth.AuthTests.post
    def setUp(self):
        test_auth.AuthTests.setUp(self)
        self.register()

    def register(self):
        return test_auth.AuthTests.register(self)

    def mutate(self, path, data=None, method='post', client=None):
        client = client or self.client
        csrf = client.get('/api/auth/csrf/').json()['csrfToken']
        return getattr(client, method)('/api/auth/' + path + '/', data or {},
            content_type='application/json', HTTP_X_CSRFTOKEN=csrf)

    def link(self, index=-1):
        return {k: v[0] for k, v in parse_qs(urlparse(mail.outbox[index].body.splitlines()[-1]).query).items()}

    def expire_reauth(self):
        session = self.client.session
        session['reauthenticated_at'] = time.time() - 601
        session.save()

    def test_f_profile_whitelist_partial_and_phone(self):
        response = self.mutate('profile', {'full_name': 'New Name', 'phone': '+90 (555) 123-4567'}, 'patch')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['phone'], '+905551234567')
        self.assertFalse(response.json()['user']['phone_verified'])
        for field, value in [('email', 'bad@example.com'), ('email_verified', True), ('phone_verified', True), ('security_version', 99)]:
            self.assertEqual(self.mutate('profile', {field: value}, 'patch').status_code, 400)
        self.assertEqual(self.mutate('profile', {'birth_date': timezone.now().date().isoformat()}, 'patch').status_code, 400)
        self.assertEqual(self.mutate('profile', {'username': 'a\u0301b'}, 'patch').status_code, 400)

    def test_f_all_protected_routes_require_session(self):
        anonymous = Client(enforce_csrf_checks=True)
        for path, method in [('profile','patch'), ('reauthenticate','post'), ('password/change','post'), ('email/resend','post'), ('email/change','post'), ('sessions/revoke','post')]:
            self.assertEqual(self.mutate(path, {}, method, anonymous).status_code, 401, path)
        self.assertEqual(anonymous.get('/api/auth/sessions/').status_code, 401)

    def test_f_all_mutations_require_csrf(self):
        anonymous = Client(enforce_csrf_checks=True)
        for path, method in [('profile','patch'), ('reauthenticate','post'), ('password/change','post'), ('password/reset','post'), ('password/reset/confirm','post'), ('email/resend','post'), ('email/change','post'), ('email/verify','post'), ('sessions/revoke','post')]:
            response = getattr(anonymous, method)('/api/auth/' + path + '/', {}, content_type='application/json')
            self.assertEqual(response.status_code, 403, path)
            self.assertEqual(response.json()['code'], 'csrf_failed')

    def test_f_verification_expiry_replay_and_get_no_mutation(self):
        key = self.link()['key']
        self.assertEqual(self.client.get('/api/auth/email/verify/', {'key': key}).status_code, 405)
        self.assertFalse(User.objects.get().email_verified)
        self.assertEqual(self.mutate('email/verify', {'key': key}).status_code, 200)
        self.assertTrue(User.objects.get().email_verified)
        self.assertEqual(self.mutate('email/verify', {'key': key}).json()['code'], 'invalid_token')

    def test_f_email_resend_interval_hour_budget_initial_counts(self):
        self.assertEqual(self.mutate('email/resend').status_code, 429)
        for _ in range(4):
            self.fake.expiry[security.key('mail-interval', self.data['email'])] = 0
            self.assertEqual(self.mutate('email/resend').status_code, 200)
        self.fake.expiry[security.key('mail-interval', self.data['email'])] = 0
        self.assertEqual(self.mutate('email/resend').status_code, 429)
        self.assertEqual(len(mail.outbox), 5)
        self.fake.expiry[security.key('mail-hour', self.data['email'])] = 0
        self.assertEqual(self.mutate('email/resend').status_code, 200)

    def test_f_expired_verify_token(self):
        key = self.link()['key']
        self.fake.expiry[security.key('email-verify', key)] = 0
        self.assertEqual(self.mutate('email/verify', {'key': key}).json()['code'], 'invalid_token')
        self.assertFalse(User.objects.get().email_verified)

    def test_f_reset_general_response_and_smtp_failure_no_enumeration(self):
        unknown = self.mutate('password/reset', {'email': 'none@example.com'})
        known = self.mutate('password/reset', {'email': self.data['email']})
        with patch('accounts.account_views.send_mail', side_effect=OSError('secret')):
            with self.assertLogs('accounts.account_views', level='WARNING') as logs:
                failure = self.mutate('password/reset', {'email': self.data['email']})
        self.assertEqual(unknown.json(), known.json())
        self.assertEqual(known.json(), failure.json())
        self.assertEqual(failure.status_code, 200)
        self.assertNotIn(self.data['email'], str(logs.output))
        self.assertNotIn('secret', str(logs.output))

    def test_f_reset_admission_same_for_unknown_and_known(self):
        for email in [self.data['email'], 'none@example.com']:
            for _ in range(5):
                self.assertEqual(self.mutate('password/reset', {'email': email}).status_code, 200)
            self.assertEqual(self.mutate('password/reset', {'email': email.upper()}).status_code, 429)

    def test_f_reset_confirm_validation_then_single_use_revoke(self):
        self.mutate('password/reset', {'email': self.data['email']})
        data = self.link()
        token = security.peek_token('password-reset', data['token'])
        self.assertLessEqual(self.fake.expiry[security.key('password-reset', data['token'])] - time.time(), 1800)
        self.assertEqual(self.mutate('password/reset/confirm', data | {'password': 'bad'}).status_code, 400)
        self.assertEqual(security.peek_token('password-reset', data['token']), token)
        self.assertEqual(self.mutate('password/reset/confirm', data | {'password': 'Başka9!x'}).status_code, 200)
        self.assertTrue(User.objects.get().check_password('Başka9!x'))
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])
        self.assertFalse(SessionRecord.objects.filter(revoked=False).exists())
        self.assertEqual(self.mutate('password/reset/confirm', data | {'password': 'Başka9!x'}).json()['code'], 'invalid_token')

    def test_f_reset_wrong_uid_expiry_and_version(self):
        self.mutate('password/reset', {'email': self.data['email']})
        data = self.link() | {'password': 'Başka9!x'}
        self.assertEqual(self.mutate('password/reset/confirm', data | {'uid':'9999'}).json()['code'], 'invalid_token')
        self.fake.expiry[security.key('password-reset', data['token'])] = 0
        self.assertEqual(self.mutate('password/reset/confirm', data).json()['code'], 'invalid_token')
        self.mutate('password/reset', {'email': self.data['email']})
        data = self.link() | {'password': 'Başka9!x'}
        User.objects.update(security_version=2)
        self.assertEqual(self.mutate('password/reset/confirm', data).json()['code'], 'invalid_token')

    def test_f_unusable_social_password_can_be_set_via_email_proof(self):
        user = User.objects.get()
        user.set_unusable_password()
        user.save()
        self.mutate('password/reset', {'email': self.data['email']})
        self.assertEqual(self.mutate('password/reset/confirm', self.link() | {'password':'Başka9!x'}).status_code, 200)
        self.assertTrue(User.objects.get().check_password('Başka9!x'))

    def test_f_reauth_expiry_and_shared_failure_limiter(self):
        self.expire_reauth()
        for path, data in [('email/change', {'email':'new@example.com'}), ('password/change', {'old_password': self.data['password'], 'password':'Başka9!x'}), ('sessions/revoke', {})]:
            self.assertEqual(self.mutate(path, data).json()['code'], 'reauthentication_required')
        for _ in range(5):
            self.assertEqual(self.mutate('reauthenticate', {'password':'bad'}).status_code, 400)
        self.assertEqual(self.mutate('reauthenticate', {'password':self.data['password']}).status_code, 429)
        self.assertEqual(self.mutate('login', {'email':self.data['email'], 'password':self.data['password']}).status_code, 429)

    def test_f_password_change_reauth_and_all_sessions_revoked(self):
        self.expire_reauth()
        self.assertEqual(self.mutate('reauthenticate', {'password':self.data['password']}).status_code, 200)
        self.assertEqual(self.mutate('password/change', {'old_password':'bad','password':'Başka9!x'}).status_code, 400)
        self.assertEqual(self.mutate('password/change', {'old_password':self.data['password'],'password':'Başka9!x'}).status_code, 200)
        self.assertTrue(User.objects.get().check_password('Başka9!x'))
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])

    def test_f_email_change_old_stays_active_notification_and_confirm(self):
        old_token = self.link()['key']
        self.assertEqual(self.mutate('email/change', {'email':'NEW@example.com'}).status_code, 200)
        self.assertEqual(User.objects.get().email, self.data['email'])
        self.assertEqual(mail.outbox[-1].to, [self.data['email']])
        self.assertEqual(mail.outbox[-2].to, ['new@example.com'])
        key = self.link(-2)['key']
        self.assertEqual(self.mutate('email/verify', {'key':key}).status_code, 200)
        user = User.objects.get()
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.email_verified)
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])
        self.assertEqual(self.mutate('email/verify', {'key':old_token}).json()['code'], 'invalid_token')

    def test_f_email_change_superseded_and_taken_address_no_merge(self):
        self.mutate('email/change', {'email':'first-new@example.com'})
        first = self.link(-2)['key']
        self.fake.expiry[security.key('email-change-interval', str(User.objects.get().pk))] = 0
        self.mutate('email/change', {'email':'second-new@example.com'})
        second = self.link(-2)['key']
        self.assertEqual(self.mutate('email/verify', {'key':first}).json()['code'], 'invalid_token')
        other = User.objects.create_user(email='second-new@example.com', username='other', password='Other9!x')
        self.assertEqual(self.mutate('email/verify', {'key':second}).status_code, 400)
        self.assertEqual(User.objects.get(pk=other.pk).email, 'second-new@example.com')
        self.assertEqual(User.objects.get(pk=1).email, self.data['email'])
        self.assertEqual(self.mutate('email/change', {'email':'second-new@example.com'}).status_code, 400)

    def test_f_email_change_smtp_failure_preserves_old_state(self):
        with patch('accounts.account_views.send_mail', side_effect=OSError('secret')):
            self.assertEqual(self.mutate('email/change', {'email':'new@example.com'}).status_code, 503)
        user = User.objects.get()
        self.assertEqual(user.email, self.data['email'])
        self.assertEqual(user.email_change_nonce, '')

    def test_f_sessions_ownership_listing_and_revocation(self):
        other = User.objects.create_user(email='other@example.com', username='other', password='Other9!x')
        alien = SessionRecord.objects.create(user=other, key_hash='z'*64, security_version=1, expires_at=timezone.now()+timedelta(hours=1))
        records = self.client.get('/api/auth/sessions/').json()['sessions']
        self.assertEqual(len(records), 1)
        self.assertEqual(set(records[0]), {'id','created_at','expires_at','current'})
        self.assertTrue(records[0]['current'])
        self.assertEqual(self.mutate('sessions/'+str(alien.pk), method='delete').status_code, 404)
        self.assertEqual(self.mutate('sessions/'+records[0]['id'], method='delete').status_code, 200)
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])

    def test_f_sessions_all_revoke(self):
        self.assertEqual(self.mutate('sessions/revoke').status_code, 200)
        self.assertFalse(SessionRecord.objects.filter(revoked=False).exists())
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])


    def test_f_inflight_revoked_request_cannot_issue_email_change(self):
        from accounts.account_views import locked_user
        original = locked_user
        def concurrent_revoke(request, sensitive=False):
            User.objects.filter(pk=request.user.pk).update(security_version=2)
            return original(request, sensitive=sensitive)
        with patch('accounts.account_views.locked_user', side_effect=concurrent_revoke):
            response = self.mutate('email/change', {'email':'new@example.com'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(User.objects.get().email_change_nonce, '')

    def test_f_reset_ip_admission_and_fixed_links(self):
        self.fake.set(security.key('reset-ip', '127.0.0.1'), 30, ex=900)
        self.assertEqual(self.mutate('password/reset', {'email':'none@example.com'}).status_code, 429)
        self.fake.delete(security.key('reset-ip', '127.0.0.1'))
        self.assertEqual(self.mutate('password/reset', {'email':self.data['email']}).status_code, 200)
        self.assertIn('https://first.test/sifre-sifirla?', mail.outbox[-1].body)
        self.assertIn('30 dakika', mail.outbox[-1].body)

    def test_f_session_listing_omits_expired_and_revoked(self):
        user = User.objects.get()
        SessionRecord.objects.create(user=user, key_hash='a'*64, security_version=1,
            expires_at=timezone.now()-timedelta(seconds=1))
        SessionRecord.objects.create(user=user, key_hash='b'*64, security_version=1,
            expires_at=timezone.now()+timedelta(hours=1), revoked=True)
        self.assertEqual(len(self.client.get('/api/auth/sessions/').json()['sessions']), 1)

    def test_f_two_sessions_closed_by_reset(self):
        second = Client(enforce_csrf_checks=True)
        self.assertEqual(self.mutate('login', {'email':self.data['email'], 'password':self.data['password']}, client=second).status_code, 200)
        self.assertEqual(len(self.client.get('/api/auth/sessions/').json()['sessions']), 2)
        self.mutate('password/reset', {'email':self.data['email']})
        self.assertEqual(self.mutate('password/reset/confirm', self.link() | {'password':'Başka9!x'}).status_code, 200)
        self.assertIsNone(second.get('/api/auth/me/').json()['user'])
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])

    def test_f_old_address_notification_failure_invalidates_new_link(self):
        from accounts.account_views import delivery
        def fail_old(subject, body, email):
            if email == self.data['email']:
                from accounts.views import ServiceError
                raise ServiceError()
            return delivery(subject, body, email)
        with patch('accounts.account_views.delivery', side_effect=fail_old):
            self.assertEqual(self.mutate('email/change', {'email':'new@example.com'}).status_code, 503)
        key = self.link()['key']
        self.assertEqual(self.mutate('email/verify', {'key':key}).json()['code'], 'invalid_token')
        self.assertEqual(User.objects.get().email, self.data['email'])

    def test_f_invalid_password_change_does_not_revoke_or_consume_proof(self):
        self.assertEqual(self.mutate('password/change', {'old_password':self.data['password'], 'password':'bad'}).status_code, 400)
        self.assertTrue(User.objects.get().check_password(self.data['password']))
        self.assertEqual(security.attempts('password-account', self.data['email']), 0)
        self.assertEqual(SessionRecord.objects.filter(revoked=False).count(), 1)


    def test_f_missing_empty_or_invalid_tokens_use_contract_error(self):
        for data in [{}, {'key':''}, {'key':'unknown'}]:
            self.assertEqual(self.mutate('email/verify', data).json()['code'], 'invalid_token')
        for data in [{'password':'Başka9!x'}, {'uid':'1','token':'','password':'Başka9!x'}]:
            self.assertEqual(self.mutate('password/reset/confirm', data).json()['code'], 'invalid_token')

    def test_f_resend_smtp_failure_not_hidden(self):
        self.fake.expiry[security.key('mail-interval', self.data['email'])] = 0
        with patch('accounts.views.send_mail', side_effect=OSError('secret')):
            response = self.mutate('email/resend')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'email_delivery_failed')
        self.assertNotIn('secret', response.content.decode())

    def test_f_rate_limit_uses_signed_proxy_ip_for_reset(self):
        from django.test import override_settings
        from .test_proxy import SECRET, assertion
        with override_settings(AUTH_PROXY_SECRET=SECRET):
            csrf = self.client.get('/api/auth/csrf/', **assertion('203.0.113.8', '/api/auth/csrf/', 'GET')).json()['csrfToken']
            response = self.client.post('/api/auth/password/reset/', {'email':'none@example.com'},
                content_type='application/json', HTTP_X_CSRFTOKEN=csrf,
                **assertion('203.0.113.8', '/api/auth/password/reset/', 'POST'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(security.attempts('reset-ip','203.0.113.8'), 1)
        self.assertEqual(security.attempts('reset-ip','127.0.0.1'), 0)


    def test_f_stale_login_signal_cannot_restore_old_verified_address(self):
        from django.contrib.auth.models import update_last_login
        stale = User.objects.get()
        User.objects.filter(pk=stale.pk).update(email='confirmed@example.com',
            email_verified=True, security_version=2, username='Changed', username_normalized='changed')
        update_last_login(None, stale)
        current = User.objects.get(pk=stale.pk)
        self.assertEqual(current.email, 'confirmed@example.com')
        self.assertTrue(current.email_verified)
        self.assertEqual(current.security_version, 2)
        self.assertEqual(current.username, 'Changed')
        self.assertEqual(current.username_normalized, 'changed')
        self.assertIsNotNone(current.last_login)

    def test_f_partial_username_save_normalizes_only_requested_identity(self):
        stale = User.objects.get()
        User.objects.filter(pk=stale.pk).update(email='confirmed@example.com', security_version=2)
        stale.username = 'A\u0301bc'
        stale.save(update_fields=['username'])
        current = User.objects.get(pk=stale.pk)
        self.assertEqual(current.username, 'Ábc')
        self.assertEqual(current.username_normalized, 'ábc')
        self.assertEqual(current.email, 'confirmed@example.com')
        self.assertEqual(current.security_version, 2)

    def test_f_partial_email_save_does_not_restore_stale_username(self):
        stale = User.objects.get()
        User.objects.filter(pk=stale.pk).update(username='Changed', username_normalized='changed')
        stale.email = ' NEW@example.com '
        stale.save(update_fields=['email'])
        current = User.objects.get(pk=stale.pk)
        self.assertEqual(current.email, 'new@example.com')
        self.assertEqual(current.username, 'Changed')
        self.assertEqual(current.username_normalized, 'changed')

    def test_email_change_varying_destinations_cannot_bypass_requester_interval(self):
        self.assertEqual(self.mutate('email/change', {'email': 'new0@example.com'}).status_code, 200)
        for index in range(1, 8):
            with patch('accounts.security.issue_token') as issue, patch('accounts.account_views.delivery') as send:
                response = self.mutate('email/change', {'email': f'new{index}@example.com'})
                self.assertEqual(response.status_code, 429)
                issue.assert_not_called()
                send.assert_not_called()
        self.assertEqual(len(mail.outbox), 3)  # Registration plus one notification pair.
        self.assertEqual(security.attempts('email-change-hour', str(User.objects.get().pk)), 1)
        self.assertEqual(security.attempts('email-change-ip', '127.0.0.1'), 1)

    def test_email_change_hour_budget_bounds_old_address_notifications(self):
        uid = str(User.objects.get().pk)
        for index in range(5):
            self.fake.expiry[security.key('email-change-interval', uid)] = 0
            self.assertEqual(self.mutate('email/change', {'email': f'new{index}@example.com'}).status_code, 200)
        self.fake.expiry[security.key('email-change-interval', uid)] = 0
        with patch('accounts.security.issue_token') as issue, patch('accounts.account_views.delivery') as send:
            self.assertEqual(self.mutate('email/change', {'email': 'sixth@example.com'}).status_code, 429)
            issue.assert_not_called()
            send.assert_not_called()
        self.assertEqual(len(mail.outbox), 11)
        self.assertEqual(security.attempts('email-change-ip', '127.0.0.1'), 5)
        self.fake.expiry[security.key('email-change-hour', uid)] = 0
        self.assertEqual(self.mutate('email/change', {'email': 'sixth@example.com'}).status_code, 200)

    def test_email_change_ip_budget_rejects_without_partial_account_reservation(self):
        uid = str(User.objects.get().pk)
        self.fake.set(security.key('email-change-ip', '127.0.0.1'), 30, ex=900)
        with patch('accounts.security.issue_token') as issue, patch('accounts.account_views.delivery') as send:
            self.assertEqual(self.mutate('email/change', {'email': 'new@example.com'}).status_code, 429)
            issue.assert_not_called()
            send.assert_not_called()
        self.assertFalse(self.fake.exists(security.key('email-change-interval', uid)))
        self.assertEqual(security.attempts('email-change-hour', uid), 0)
        self.fake.expiry[security.key('email-change-ip', '127.0.0.1')] = 0
        self.assertEqual(self.mutate('email/change', {'email': 'new@example.com'}).status_code, 200)

    def test_email_change_admission_redis_failure_is_closed(self):
        import redis
        original_eval = self.fake.eval

        def unavailable(script, *args):
            if 'email-change-admission' in script:
                raise redis.ConnectionError('unavailable')
            return original_eval(script, *args)

        with patch.object(self.fake, 'eval', side_effect=unavailable), \
                patch('accounts.security.issue_token') as issue, \
                patch('accounts.account_views.delivery') as send:
            response = self.mutate('email/change', {'email': 'new@example.com'})
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()['code'], 'service_unavailable')
            issue.assert_not_called()
            send.assert_not_called()
        self.assertEqual(User.objects.get().email_change_nonce, '')
