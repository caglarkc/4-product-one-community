"""GitHub authorization-code login/link; provider tokens remain transient server-side."""
import base64
import hashlib
import json
import secrets
import time
from urllib.parse import urlencode

import requests
from allauth.socialaccount.models import SocialAccount
from .connected_accounts import provider_metadata, save_metadata
from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.exceptions import APIException, NotAuthenticated, ValidationError
from rest_framework.response import Response

from . import security
from .account_views import locked_user, revoke_all, recent
from .models import User
from .proxy import client_ip
from .serializers import StrictSerializer, ProfileSerializer, user_data
from .views import AuthView, RateLimited, ServiceError, start_session

TTL = 600
AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"


class GitHubError(APIException):
    status_code = 400
    default_detail = {'detail': 'GitHub girişi tamamlanamadı. Yeniden deneyin.', 'code': 'github_auth_failed'}


def enabled():
    return bool(settings.GITHUB_ENABLED and settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET and settings.GITHUB_REDIRECT_URI)


def require_enabled():
    if not enabled():
        raise ServiceError({'detail': 'GitHub girişi şu anda kullanılamıyor.', 'code': 'github_unavailable'})


class StartInput(StrictSerializer):
    remember_me = serializers.BooleanField(default=False)
    purpose = serializers.ChoiceField(choices=['login', 'link', 'reauth'], default='login')

    def validate_remember_me(self, value):
        if type(self.initial_data.get('remember_me', False)) is not bool:
            raise serializers.ValidationError('Boolean gereklidir.')
        return value


class SignupInput(ProfileSerializer):
    email = serializers.EmailField(max_length=254, required=False)


def exchange(code, flow):
    """Exchange code with PKCE, then fetch identity and verified primary email over TLS."""
    try:
        response = requests.post(ACCESS_TOKEN_URL, data={
            'client_id': settings.GITHUB_CLIENT_ID, 'client_secret': settings.GITHUB_CLIENT_SECRET,
            'code': code, 'code_verifier': flow['verifier'],
            'redirect_uri': settings.GITHUB_REDIRECT_URI,
        }, headers={'Accept': 'application/json'}, timeout=10, allow_redirects=False)
        response.raise_for_status()
        credential = response.json()
        token = credential.get('access_token')
        if (response.status_code != 200 or credential.get('error') or not isinstance(token, str)
                or not token or credential.get('token_type', '').lower() != 'bearer'):
            raise GitHubError()
        headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                   'X-GitHub-Api-Version': '2022-11-28'}
        response = requests.get('https://api.github.com/user', headers=headers, timeout=10, allow_redirects=False)
        response.raise_for_status()
        claims = response.json()
        if response.status_code != 200 or type(claims.get('id')) is not int or claims['id'] <= 0:
            raise GitHubError()
        # Fixed endpoint; no arbitrary provider URL or pagination link is followed.
        response = requests.get('https://api.github.com/user/emails', headers=headers,
                                params={'per_page': 100}, timeout=10, allow_redirects=False)
        response.raise_for_status()
        emails = response.json()
        if response.status_code != 200 or not isinstance(emails, list):
            raise GitHubError()
        primary = next((row for row in emails if isinstance(row, dict) and
                        row.get('primary') is True and row.get('verified') is True), {})
        return {**claims, 'verified_primary_email': primary.get('email', '')}
    except (requests.RequestException, KeyError, ValueError, TypeError, AttributeError) as exc:
        raise GitHubError() from exc


def identity_profile(claims):
    email = str(claims.get('verified_primary_email') or '').strip().lower()
    try:
        email = serializers.EmailField(max_length=254).run_validation(email)
    except ValidationError:
        email = ''
    return {'display': provider_metadata('github', claims), 'sub': str(claims['id']), 'email': email, 'trusted': bool(email),
            'full_name': str(claims.get('name') or '')[:150],
            'username': str(claims.get('login') or '').replace('-', '_')[:30]}


def github_session(request, user, remember):
    start_session(request, user, remember)
    # OAuth authorization can silently reuse an old GitHub browser session.
    request.session.pop('reauthenticated_at', None)


class GitHubStartView(AuthView):
    def post(self, request):
        require_enabled()
        if security.count('github-start-ip', client_ip(request)) > settings.AUTH_IP_ATTEMPTS:
            raise RateLimited()
        serializer = StartInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data['purpose'] == 'reauth':
            raise GitHubError({'detail': 'Şifre veya bağlı Google hesabınızla yeniden doğrulayın.',
                               'code': 'github_reauth_unavailable'})
        if data['purpose'] == 'link':
            if not request.user.is_authenticated:
                raise NotAuthenticated()
            recent(request)
        if not request.session.session_key:
            request.session.create()
        binder = secrets.token_urlsafe(32)
        request.session['github_binder'] = binder
        verifier = secrets.token_urlsafe(48)
        flow = {**data, 'binder': binder, 'verifier': verifier, 'session_hash': security.digest(request.session.session_key),
                'user_id': request.user.pk if request.user.is_authenticated else None,
                'security_version': request.user.security_version if request.user.is_authenticated else None,
                'started_at': time.time()}
        state = security.issue_token('github-state', flow, TTL)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        params = {'client_id': settings.GITHUB_CLIENT_ID, 'redirect_uri': settings.GITHUB_REDIRECT_URI,
                  'scope': 'user:email', 'state': state,
                  'code_challenge': challenge, 'code_challenge_method': 'S256', 'prompt': 'select_account'}
        return Response({'authorization_url': AUTHORIZE_URL + '?' + urlencode(params)})


class GitHubCallbackView(AuthView):
    def get(self, request):
        require_enabled()
        state = request.query_params.get('state', '')
        if not state or len(state) > 128 or len(request.query_params.getlist('state')) != 1:
            raise GitHubError()
        flow = security.peek_token('github-state', state)
        binder = request.session.get('github_binder', '')
        if not flow or not binder or not secrets.compare_digest(flow['binder'], binder):
            raise GitHubError()
        if security.consume_token('github-state', state) != flow:
            raise GitHubError()
        request.session.pop('github_binder', None)
        if request.query_params.get('error'):
            raise GitHubError({'detail': 'GitHub girişi iptal edildi.', 'code': 'github_cancelled'})
        code = request.query_params.get('code', '')
        if not code or len(code) > 4096 or len(request.query_params.getlist('code')) != 1:
            raise GitHubError()
        profile = identity_profile(exchange(code, flow))
        try:
            with transaction.atomic():
                if flow.get('user_id') is not None:
                    if not request.user.is_authenticated or request.user.pk != flow['user_id']:
                        raise GitHubError()
                    flow_user = locked_user(request)
                    if flow_user.security_version != flow.get('security_version'):
                        raise GitHubError()
                identity = SocialAccount.objects.select_related('user').filter(provider='github', uid=profile['sub']).first()
                if flow['purpose'] == 'link':
                    if (not request.user.is_authenticated or request.user.pk != flow['user_id']
                            or security.digest(request.session.session_key) != flow['session_hash']):
                        raise GitHubError()
                    user = locked_user(request, sensitive=True)
                    if user.security_version != flow['security_version']:
                        raise GitHubError()
                    # Re-read only after the user lock; never transfer or replace an identity.
                    identity = SocialAccount.objects.filter(provider='github', uid=profile['sub']).first()
                    linked = SocialAccount.objects.filter(provider='github', user=user).first()
                    if (identity and identity.user_id != user.pk) or (linked and linked.uid != profile['sub']):
                        raise GitHubError({'detail': 'GitHub hesabı başka bir hesaba bağlı veya hesabınızda farklı bir GitHub bağlantısı var.',
                                           'code': 'github_link_conflict'})
                    if not identity:
                        SocialAccount.objects.create(user=user, provider='github', uid=profile['sub'])
                    save_metadata(user, 'github', profile)
                    return Response({'status': 'linked', 'user': user_data(user)})
                if identity:
                    try:
                        user = User.objects.select_for_update().get(pk=identity.user_id)
                    except User.DoesNotExist:
                        raise GitHubError() from None
                    # Recovery may remove this identity while we wait for the user lock.
                    if not SocialAccount.objects.filter(pk=identity.pk, provider='github',
                                                        uid=profile['sub'], user=user).exists():
                        raise GitHubError()
                elif profile['trusted']:
                    user = User.objects.select_for_update().filter(email=profile['email']).first()
                else:
                    user = None
                if user:
                    if not user.is_active:
                        raise GitHubError()
                    if not identity:
                        if not user.email_verified:
                            revoke_all(user)
                            # Remove identities added before this mailbox owner proved ownership.
                            SocialAccount.objects.filter(user=user).delete()
                            user.set_unusable_password()
                            user.email_verified = True
                            user.save(update_fields=['password', 'email_verified'])
                        if SocialAccount.objects.filter(user=user, provider='github').exists():
                            raise GitHubError({'detail': 'Hesabınızda farklı bir GitHub bağlantısı var.',
                                               'code': 'github_link_conflict'})
                        SocialAccount.objects.create(user=user, provider='github', uid=profile['sub'])
                    save_metadata(user, 'github', profile)
                    github_session(request, user, flow['remember_me'])
                    request.session.pop('github_signup', None)
                    return Response({'status': 'authenticated', 'user': user_data(user)})
                pending = {**profile, 'remember_me': flow['remember_me'], 'binder': secrets.token_urlsafe(32)}
                token = security.issue_token('github-signup', pending, TTL)
                request.session['github_signup'] = {'token': token, 'binder': pending['binder']}
                return Response({'status': 'profile_required'})
        except IntegrityError as exc:
            raise GitHubError() from exc


def pending_signup(request):
    reference = request.session.get('github_signup') or {}
    token = reference.get('token', '')
    pending = security.peek_token('github-signup', token) if token else None
    if not pending or pending.get('binder') != reference.get('binder'):
        raise GitHubError({'detail': 'Kayıt süresi doldu. GitHub ile yeniden başlayın.', 'code': 'github_signup_expired'})
    return token, pending


class GitHubSignupView(AuthView):
    def get(self, request):
        require_enabled()
        _, pending = pending_signup(request)
        return Response({'profile': {'email': pending['email'], 'full_name': pending['full_name'],
            'username': pending.get('username', ''), 'birth_date': '', 'gender': '', 'phone': ''},
            'email_verified': pending['trusted'], 'email_editable': not pending['trusted']})

    def post(self, request):
        require_enabled()
        if security.count('github-signup-ip', client_ip(request)) > settings.AUTH_IP_ATTEMPTS:
            raise RateLimited()
        token, pending = pending_signup(request)
        if not pending['trusted']:
            raise GitHubError({'detail': 'Kaydı tamamlamadan önce e-posta adresinizi doğrulayın.',
                               'code': 'email_verification_required'})
        serializer = SignupInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        submitted_email = data.pop('email', '').strip().lower()
        email = pending['email'] if pending['trusted'] else submitted_email or pending['email']
        if not email or (pending['trusted'] and submitted_email and submitted_email != email):
            raise ValidationError({'email': ['Geçerli e-posta adresini kullanın.']})
        # New signup never silently merges a race winner or an untrusted address.
        if User.objects.filter(email=email).exists():
            raise ValidationError({'email': ['Bu e-posta kullanılıyor. Mevcut hesabınızla giriş yapın.']})
        owner = security.acquire_password_lock('github-signup:' + token)
        if not owner:
            raise RateLimited()
        try:
            with transaction.atomic():
                if security.peek_token('github-signup', token) != pending:
                    raise GitHubError()
                user = User.objects.create_user(email=email, email_verified=pending['trusted'], **data)
                SocialAccount.objects.create(user=user, provider='github', uid=pending['sub'])
                if security.consume_token('github-signup', token) != pending:
                    raise GitHubError()
                request.session.pop('github_signup', None)
                save_metadata(user, 'github', pending)
                github_session(request, user, pending['remember_me'])
        except IntegrityError as exc:
            raise ValidationError({'non_field_errors': ['Hesap veya kullanıcı adı kullanılıyor. GitHub ile yeniden başlayın.']}) from exc
        finally:
            security.release_password_lock('github-signup:' + token, owner)
        return Response({'user': user_data(user)}, status=201)


class GitHubEmailInput(StrictSerializer):
    email = serializers.EmailField(max_length=254)


class GitHubEmailVerifyInput(StrictSerializer):
    key = serializers.CharField(max_length=128)


class GitHubEmailRequestView(AuthView):
    def post(self, request):
        from .account_views import delivery
        require_enabled()
        signup_token, pending = pending_signup(request)
        if pending['trusted']:
            raise GitHubError()
        serializer = GitHubEmailInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()
        if security.count('github-email-ip', client_ip(request)) > settings.AUTH_IP_ATTEMPTS:
            raise RateLimited()
        if not security.reserve_verification_email(email):
            raise RateLimited()
        user = User.objects.filter(email=email).first()
        payload = {'signup_token': signup_token, 'email': email, 'sub': pending['sub'],
                   'user_id': user.pk if user else None,
                   'security_version': user.security_version if user else None}
        token = security.issue_token('github-email', payload, TTL)
        link = settings.FRONTEND_ORIGIN + '/github-eposta-dogrula?' + urlencode({'key': token})
        try:
            delivery('FIRST GitHub girişi için e-posta doğrulama',
                     'GitHub girişini başlattığınız tarayıcıda bağlantıyı açıp onaylayın.\n'
                     'Bağlantı 10 dakika geçerlidir. Bu işlemi siz başlatmadıysanız onaylamayın.\n' + link, email)
        except ServiceError:
            security.consume_token('github-email', token)
            raise
        return Response({'detail': 'GitHub girişini tamamlamak için e-posta doğrulama bağlantısı gönderildi.'})


class GitHubEmailVerifyView(AuthView):
    def post(self, request):
        require_enabled()
        signup_token, pending = pending_signup(request)
        serializer = GitHubEmailVerifyInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['key']
        proof = security.peek_token('github-email', token)
        if not proof or proof['signup_token'] != signup_token or proof['sub'] != pending['sub']:
            raise GitHubError()
        owner = security.acquire_password_lock('github-signup:' + signup_token)
        if not owner:
            raise RateLimited()
        try:
            with transaction.atomic():
                if security.peek_token('github-signup', signup_token) != pending:
                    raise GitHubError()
                user = User.objects.select_for_update().filter(email=proof['email']).first()
                if ((user.pk if user else None) != proof['user_id']
                        or (user and (not user.is_active or user.security_version != proof['security_version']))):
                    raise GitHubError()
                if security.consume_token('github-email', token) != proof:
                    raise GitHubError()
                if not user:
                    pending.update(email=proof['email'], trusted=True)
                    security.execute('set', security.key('github-signup', signup_token),
                                     json.dumps(pending), ex=TTL)
                    return Response({'status': 'profile_required'})
                identity = SocialAccount.objects.filter(provider='github', uid=pending['sub']).first()
                if identity and identity.user_id != user.pk:
                    raise GitHubError()
                if not user.email_verified:
                    revoke_all(user)
                    SocialAccount.objects.filter(user=user).delete()
                    user.set_unusable_password()
                    user.email_verified = True
                    user.save(update_fields=['password', 'email_verified'])
                    identity = None
                if not identity:
                    if SocialAccount.objects.filter(user=user, provider='github').exists():
                        raise GitHubError({'detail': 'Hesabınızda farklı bir GitHub bağlantısı var.',
                                           'code': 'github_link_conflict'})
                    SocialAccount.objects.create(user=user, provider='github', uid=pending['sub'])
                if security.consume_token('github-signup', signup_token) != pending:
                    raise GitHubError()
                request.session.pop('github_signup', None)
                save_metadata(user, 'github', pending)
                github_session(request, user, pending['remember_me'])
                return Response({'status': 'authenticated', 'user': user_data(user)})
        except IntegrityError as exc:
            raise GitHubError() from exc
        finally:
            security.release_password_lock('github-signup:' + signup_token, owner)
