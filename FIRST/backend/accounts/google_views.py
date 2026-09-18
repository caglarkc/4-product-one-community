"""Google authorization-code login; never exposes provider tokens to the browser."""
import base64
import hashlib
import json
import secrets
import time
from types import SimpleNamespace
from urllib.parse import urlencode

import requests
from allauth.socialaccount.models import SocialAccount
from .connected_accounts import provider_metadata, save_metadata
from allauth.socialaccount.providers.google.views import AUTHORIZE_URL, ACCESS_TOKEN_URL, _verify_and_decode
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.exceptions import APIException, NotAuthenticated, ValidationError
from rest_framework.response import Response

from . import security
from .account_views import locked_user, revoke_all
from .models import User
from .proxy import client_ip
from .serializers import StrictSerializer, ProfileSerializer, user_data
from .views import AuthView, RateLimited, ServiceError, start_session

TTL = 600


class GoogleError(APIException):
    status_code = 400
    default_detail = {'detail': 'Google girişi tamamlanamadı. Yeniden deneyin.', 'code': 'google_auth_failed'}


def enabled():
    return bool(settings.GOOGLE_ENABLED and settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET and settings.GOOGLE_REDIRECT_URI)


def require_enabled():
    if not enabled():
        raise ServiceError({'detail': 'Google girişi şu anda kullanılamıyor.', 'code': 'google_unavailable'})


def redirect_uri_for_request(request):
    # AuthView has already enforced CSRF, including the Origin allowlist.
    # The local origin additionally requires its own explicit OAuth opt-in.
    origin = request.headers.get('Origin', '')
    if origin == 'http://127.0.0.1:3101' and settings.GOOGLE_LOCAL_REDIRECT_URI:
        return settings.GOOGLE_LOCAL_REDIRECT_URI
    if origin and origin != settings.FRONTEND_ORIGIN:
        raise GoogleError()
    return settings.GOOGLE_REDIRECT_URI


class StartInput(StrictSerializer):
    remember_me = serializers.BooleanField(default=False)
    purpose = serializers.ChoiceField(choices=['login', 'reauth'], default='login')

    def validate_remember_me(self, value):
        if type(self.initial_data.get('remember_me', False)) is not bool:
            raise serializers.ValidationError('Boolean gereklidir.')
        return value


class SignupInput(ProfileSerializer):
    email = serializers.EmailField(max_length=254, required=False)


def exchange(code, flow):
    """TLS code exchange + allauth signature/issuer/audience/expiry verification."""
    try:
        # Missing keys are only for production flows started before this release.
        redirect_uri = flow.get('redirect_uri', settings.GOOGLE_REDIRECT_URI)
        if not redirect_uri or redirect_uri not in (settings.GOOGLE_REDIRECT_URI, settings.GOOGLE_LOCAL_REDIRECT_URI):
            raise GoogleError()
        response = requests.post(ACCESS_TOKEN_URL, data={
            'client_id': settings.GOOGLE_CLIENT_ID, 'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'code': code, 'code_verifier': flow['verifier'], 'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        }, timeout=10)
        response.raise_for_status()
        credential = response.json()['id_token']
        claims = _verify_and_decode(SimpleNamespace(client_id=settings.GOOGLE_CLIENT_ID), credential,
                                    verify_signature=True)
        if (not isinstance(claims.get('sub'), str) or not claims['sub'] or len(claims['sub']) > 191
                or not isinstance(claims.get('nonce'), str)
                or not secrets.compare_digest(claims['nonce'], flow['nonce'])
                or not claims.get('exp') or not claims.get('iat')
                or claims.get('azp', settings.GOOGLE_CLIENT_ID) != settings.GOOGLE_CLIENT_ID):
            raise GoogleError()
        if flow.get('purpose') == 'reauth':
            auth_time = claims.get('auth_time')
            if not isinstance(auth_time, (int, float)) or not flow['started_at'] - 60 <= auth_time <= time.time() + 60:
                raise GoogleError()
        return claims
    except (requests.RequestException, OAuth2Error, KeyError, ValueError, TypeError) as exc:
        raise GoogleError() from exc


def identity_profile(claims):
    email = str(claims.get('email') or '').strip().lower()
    try:
        email = serializers.EmailField(max_length=254).run_validation(email)
    except ValidationError:
        email = ''
    # Google is authoritative for Gmail and verified Workspace domains only.
    trusted = bool(email and claims.get('email_verified') is True and
                   (email.endswith('@gmail.com') or bool(claims.get('hd'))))
    return {'display': provider_metadata('google', claims), 'sub': claims['sub'], 'email': email, 'trusted': trusted,
            'full_name': str(claims.get('name') or '')[:150]}


class GoogleStartView(AuthView):
    def post(self, request):
        require_enabled()
        if security.count('google-start-ip', client_ip(request)) > settings.AUTH_IP_ATTEMPTS:
            raise RateLimited()
        serializer = StartInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        redirect_uri = redirect_uri_for_request(request)
        if data['purpose'] == 'reauth' and not request.user.is_authenticated:
            raise NotAuthenticated()
        if not request.session.session_key:
            request.session.create()
        binder = secrets.token_urlsafe(32)
        request.session['google_binder'] = binder
        nonce, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
        flow = {**data, 'binder': binder, 'nonce': nonce, 'verifier': verifier,
                'user_id': request.user.pk if request.user.is_authenticated else None,
                'security_version': request.user.security_version if request.user.is_authenticated else None,
                'started_at': time.time(), 'redirect_uri': redirect_uri}
        state = security.issue_token('google-state', flow, TTL)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        params = {'client_id': settings.GOOGLE_CLIENT_ID, 'redirect_uri': redirect_uri,
                  'response_type': 'code', 'scope': 'openid email profile', 'state': state, 'nonce': nonce,
                  'code_challenge': challenge, 'code_challenge_method': 'S256', 'prompt': 'select_account'}
        if data['purpose'] == 'reauth':
            params['max_age'] = '0'
        return Response({'authorization_url': AUTHORIZE_URL + '?' + urlencode(params)})


class GoogleCallbackView(AuthView):
    def get(self, request):
        require_enabled()
        state = request.query_params.get('state', '')
        if not state or len(state) > 128 or len(request.query_params.getlist('state')) != 1:
            raise GoogleError()
        flow = security.peek_token('google-state', state)
        binder = request.session.get('google_binder', '')
        if not flow or not binder or not secrets.compare_digest(flow['binder'], binder):
            raise GoogleError()
        if security.consume_token('google-state', state) != flow:
            raise GoogleError()
        request.session.pop('google_binder', None)
        if request.query_params.get('error'):
            raise GoogleError({'detail': 'Google girişi iptal edildi.', 'code': 'google_cancelled'})
        code = request.query_params.get('code', '')
        if not code or len(code) > 4096 or len(request.query_params.getlist('code')) != 1:
            raise GoogleError()
        profile = identity_profile(exchange(code, flow))
        try:
            with transaction.atomic():
                identity = SocialAccount.objects.select_related('user').filter(provider='google', uid=profile['sub']).first()
                if flow['purpose'] == 'reauth':
                    if (not request.user.is_authenticated or request.user.pk != flow['user_id']
                            or not identity or identity.user_id != request.user.pk):
                        raise GoogleError()
                    user = locked_user(request)
                    if not SocialAccount.objects.filter(pk=identity.pk, user=user,
                                                        provider='google', uid=profile['sub']).exists():
                        raise GoogleError()
                    if user.security_version != flow['security_version']:
                        raise GoogleError()
                    save_metadata(user, 'google', profile)
                    request.session['reauthenticated_at'] = time.time()
                    return Response({'status': 'reauthenticated', 'user': user_data(user)})
                if identity:
                    user = User.objects.select_for_update().get(pk=identity.user_id)
                    # Recovery may remove this identity while we wait for the user lock.
                    if not SocialAccount.objects.filter(pk=identity.pk, provider='google',
                                                        uid=profile['sub'], user=user).exists():
                        raise GoogleError()
                elif profile['trusted']:
                    user = User.objects.select_for_update().filter(email=profile['email']).first()
                else:
                    user = None
                if user:
                    if not user.is_active:
                        raise GoogleError()
                    if not identity:
                        if not user.email_verified:
                            revoke_all(user)
                            # Remove identities added before this mailbox owner proved ownership.
                            SocialAccount.objects.filter(user=user).delete()
                            user.set_unusable_password()
                            user.email_verified = True
                            user.save(update_fields=['password', 'email_verified'])
                        SocialAccount.objects.create(user=user, provider='google', uid=profile['sub'])
                    save_metadata(user, 'google', profile)
                    start_session(request, user, flow['remember_me'])
                    request.session.pop('google_signup', None)
                    return Response({'status': 'authenticated', 'user': user_data(user)})
                pending = {**profile, 'remember_me': flow['remember_me'], 'binder': secrets.token_urlsafe(32)}
                token = security.issue_token('google-signup', pending, TTL)
                request.session['google_signup'] = {'token': token, 'binder': pending['binder']}
                return Response({'status': 'profile_required'})
        except IntegrityError as exc:
            raise GoogleError() from exc


def pending_signup(request):
    reference = request.session.get('google_signup') or {}
    token = reference.get('token', '')
    pending = security.peek_token('google-signup', token) if token else None
    if not pending or pending.get('binder') != reference.get('binder'):
        raise GoogleError({'detail': 'Kayıt süresi doldu. Google ile yeniden başlayın.', 'code': 'google_signup_expired'})
    return token, pending


class GoogleSignupView(AuthView):
    def get(self, request):
        require_enabled()
        _, pending = pending_signup(request)
        return Response({'profile': {'email': pending['email'], 'full_name': pending['full_name'],
            'username': '', 'birth_date': '', 'gender': '', 'phone': ''},
            'email_verified': pending['trusted'], 'email_editable': not pending['trusted']})

    def post(self, request):
        require_enabled()
        if security.count('google-signup-ip', client_ip(request)) > settings.AUTH_IP_ATTEMPTS:
            raise RateLimited()
        token, pending = pending_signup(request)
        if not pending['trusted']:
            raise GoogleError({'detail': 'Kaydı tamamlamadan önce e-posta adresinizi doğrulayın.',
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
        owner = security.acquire_password_lock('google-signup:' + token)
        if not owner:
            raise RateLimited()
        try:
            with transaction.atomic():
                if security.peek_token('google-signup', token) != pending:
                    raise GoogleError()
                user = User.objects.create_user(email=email, email_verified=pending['trusted'], **data)
                SocialAccount.objects.create(user=user, provider='google', uid=pending['sub'])
                if security.consume_token('google-signup', token) != pending:
                    raise GoogleError()
                request.session.pop('google_signup', None)
                save_metadata(user, 'google', pending)
                start_session(request, user, pending['remember_me'])
        except IntegrityError as exc:
            raise ValidationError({'non_field_errors': ['Hesap veya kullanıcı adı kullanılıyor. Google ile yeniden başlayın.']}) from exc
        finally:
            security.release_password_lock('google-signup:' + token, owner)
        return Response({'user': user_data(user)}, status=201)


class GoogleEmailInput(StrictSerializer):
    email = serializers.EmailField(max_length=254)


class GoogleEmailVerifyInput(StrictSerializer):
    key = serializers.CharField(max_length=128)


class GoogleEmailRequestView(AuthView):
    def post(self, request):
        from .account_views import delivery
        require_enabled()
        signup_token, pending = pending_signup(request)
        if pending['trusted']:
            raise GoogleError()
        serializer = GoogleEmailInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].strip().lower()
        if security.count('google-email-ip', client_ip(request)) > settings.AUTH_IP_ATTEMPTS:
            raise RateLimited()
        if not security.reserve_verification_email(email):
            raise RateLimited()
        user = User.objects.filter(email=email).first()
        payload = {'signup_token': signup_token, 'email': email, 'sub': pending['sub'],
                   'user_id': user.pk if user else None,
                   'security_version': user.security_version if user else None}
        token = security.issue_token('google-email', payload, TTL)
        link = settings.FRONTEND_ORIGIN + '/google-eposta-dogrula?' + urlencode({'key': token})
        try:
            delivery('FIRST Google girişi için e-posta doğrulama',
                     'Google girişini başlattığınız tarayıcıda bağlantıyı açıp onaylayın.\n'
                     'Bağlantı 10 dakika geçerlidir. Bu işlemi siz başlatmadıysanız onaylamayın.\n' + link, email)
        except ServiceError:
            security.consume_token('google-email', token)
            raise
        return Response({'detail': 'Google girişini tamamlamak için e-posta doğrulama bağlantısı gönderildi.'})


class GoogleEmailVerifyView(AuthView):
    def post(self, request):
        require_enabled()
        signup_token, pending = pending_signup(request)
        serializer = GoogleEmailVerifyInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['key']
        proof = security.peek_token('google-email', token)
        if not proof or proof['signup_token'] != signup_token or proof['sub'] != pending['sub']:
            raise GoogleError()
        owner = security.acquire_password_lock('google-signup:' + signup_token)
        if not owner:
            raise RateLimited()
        try:
            with transaction.atomic():
                if security.peek_token('google-signup', signup_token) != pending:
                    raise GoogleError()
                user = User.objects.select_for_update().filter(email=proof['email']).first()
                if ((user.pk if user else None) != proof['user_id']
                        or (user and (not user.is_active or user.security_version != proof['security_version']))):
                    raise GoogleError()
                if security.consume_token('google-email', token) != proof:
                    raise GoogleError()
                if not user:
                    pending.update(email=proof['email'], trusted=True)
                    security.execute('set', security.key('google-signup', signup_token),
                                     json.dumps(pending), ex=TTL)
                    return Response({'status': 'profile_required'})
                identity = SocialAccount.objects.filter(provider='google', uid=pending['sub']).first()
                if identity and identity.user_id != user.pk:
                    raise GoogleError()
                if not user.email_verified:
                    revoke_all(user)
                    SocialAccount.objects.filter(user=user).delete()
                    user.set_unusable_password()
                    user.email_verified = True
                    user.save(update_fields=['password', 'email_verified'])
                    identity = None
                if not identity:
                    SocialAccount.objects.create(user=user, provider='google', uid=pending['sub'])
                if security.consume_token('google-signup', signup_token) != pending:
                    raise GoogleError()
                request.session.pop('google_signup', None)
                save_metadata(user, 'google', pending)
                start_session(request, user, pending['remember_me'])
                return Response({'status': 'authenticated', 'user': user_data(user)})
        except IntegrityError as exc:
            raise GoogleError() from exc
        finally:
            security.release_password_lock('google-signup:' + signup_token, owner)
