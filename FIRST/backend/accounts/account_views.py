"""Account operations: transactional durable changes, purpose-bound Redis tokens."""
import logging
import secrets
import time
from urllib.parse import urlencode
from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import APIException, NotFound, NotAuthenticated, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from . import security
from .models import User, SessionRecord
from .proxy import client_ip
from .serializers import StrictSerializer, ProfileSerializer, password_policy, user_data
from .views import AuthView, RateLimited, ServiceError, check_password_proof, send_verification

logger = logging.getLogger(__name__)


class InvalidToken(APIException):
    status_code = 400
    default_detail = {'detail': 'Bağlantı geçersiz, kullanılmış veya süresi dolmuş.', 'code': 'invalid_token'}


class ReauthRequired(APIException):
    status_code = 403
    default_detail = {'detail': 'Devam etmek için şifrenizi yeniden doğrulayın.', 'code': 'reauthentication_required'}


class ProtectedView(AuthView):
    permission_classes = [IsAuthenticated]


def recent(request):
    age = time.time() - request.session.get('reauthenticated_at', 0)
    if not 0 <= age <= 600:
        raise ReauthRequired()


def locked_user(request, sensitive=False):
    user = User.objects.select_for_update().get(pk=request.user.pk)
    if (not user.is_active or user.security_version != request.user.security_version
            or not SessionRecord.objects.filter(user=user, key_hash=security.digest(request.session.session_key),
                revoked=False, expires_at__gt=timezone.now(), security_version=user.security_version).exists()):
        raise NotAuthenticated('Oturum sona erdi. Yeniden giriş yapın.')
    if sensitive:
        recent(request)
    return user


def validated(serializer, request, **kwargs):
    instance = serializer(data=request.data, **kwargs)
    instance.is_valid(raise_exception=True)
    return instance.validated_data


def revoke_all(user):
    user.security_version += 1
    user.email_change_nonce = ''
    user.save(update_fields=['security_version', 'email_change_nonce'])
    SessionRecord.objects.filter(user=user, revoked=False).update(revoked=True)


def token_user(purpose, token, uid=None):
    payload = security.peek_token(purpose, token)
    if not payload or (uid is not None and str(payload['user_id']) != uid):
        raise InvalidToken()
    user = User.objects.select_for_update().filter(pk=payload['user_id'], is_active=True).first()
    if not user or user.email != payload.get('email') or user.security_version != payload.get('security_version'):
        raise InvalidToken()
    return user, payload


def require_token_fields(data, *fields):
    if not isinstance(data, dict):
        raise InvalidToken()
    for field in fields:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 128:
            raise InvalidToken()


def consume(purpose, token, payload):
    if security.consume_token(purpose, token) != payload:
        raise InvalidToken()


def delivery(subject, body, email):
    try:
        if send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False) != 1:
            raise RuntimeError('Delivery not accepted')
    except Exception as exc:
        raise ServiceError({'detail': 'E-posta gönderilemedi. Yeniden deneyin.', 'code': 'email_delivery_failed'}) from exc


class EmailInput(StrictSerializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        return value.strip().lower()


class PasswordInput(StrictSerializer):
    password = serializers.CharField(trim_whitespace=False, max_length=256)


class PasswordChangeInput(PasswordInput):
    old_password = serializers.CharField(trim_whitespace=False, max_length=256)
    password = serializers.CharField(trim_whitespace=False, validators=[password_policy])


class ResetConfirmInput(StrictSerializer):
    uid = serializers.CharField(max_length=32)
    token = serializers.CharField(max_length=128)
    password = serializers.CharField(trim_whitespace=False, validators=[password_policy])


class VerifyInput(StrictSerializer):
    key = serializers.CharField(max_length=128)


class ReauthenticateView(ProtectedView):
    def post(self, request):
        data = validated(PasswordInput, request)
        with transaction.atomic():
            user = locked_user(request)
            if not check_password_proof(request, user.email, data['password'], user):
                return Response({'detail': 'E-posta veya şifre hatalı.'}, status=400)
            request.session['reauthenticated_at'] = time.time()
        return Response({'detail': 'Kimliğiniz yeniden doğrulandı.'})


class PasswordChangeView(ProtectedView):
    def post(self, request):
        recent(request)
        data = validated(PasswordChangeInput, request)
        with transaction.atomic():
            user = locked_user(request, sensitive=True)
            if not check_password_proof(request, user.email, data['old_password'], user):
                return Response({'detail': 'E-posta veya şifre hatalı.'}, status=400)
            user.set_password(data['password'])
            user.save(update_fields=['password'])
            revoke_all(user)
        return Response({'detail': 'Şifre değiştirildi. Yeniden giriş yapın.'})


class PasswordResetView(AuthView):
    def post(self, request):
        email = validated(EmailInput, request)['email']
        if security.count('reset-ip', client_ip(request)) > 30:
            raise RateLimited()
        if security.count('reset-address', email, 3600) > 5:
            raise RateLimited()
        user = User.objects.filter(email=email, is_active=True).first()
        if user:
            token = security.issue_token('password-reset', {'user_id': user.pk, 'email': user.email,
                'security_version': user.security_version}, 1800)
            link = settings.FRONTEND_ORIGIN + '/sifre-sifirla?' + urlencode({'uid': str(user.pk), 'token': token})
            try:
                delivery('FIRST şifre sıfırlama', 'Şifrenizi sıfırlamak için bağlantıyı açıp formu gönderin.\n'
                    'Bağlantı 30 dakika geçerli ve tek kullanımlıktır.\n' + link, user.email)
            except ServiceError:
                security.execute('delete', security.key('password-reset', token))
                logger.warning('Password reset email delivery failed')  # No address/token/error secrets.
        return Response({'detail': 'Hesap uygunsa şifre sıfırlama bağlantısı gönderildi.'})


class PasswordResetConfirmView(AuthView):
    def post(self, request):
        # Field/password validation precedes token consumption so mistakes are retryable.
        require_token_fields(request.data, 'uid', 'token')
        data = validated(ResetConfirmInput, request)
        with transaction.atomic():
            user, payload = token_user('password-reset', data['token'], data['uid'])
            consume('password-reset', data['token'], payload)
            user.set_password(data['password'])
            user.save(update_fields=['password'])
            revoke_all(user)
        return Response({'detail': 'Şifre sıfırlandı. Yeniden giriş yapın.'})


class ProfileView(ProtectedView):
    def patch(self, request):
        try:
            with transaction.atomic():
                user = locked_user(request)
                data = validated(ProfileSerializer, request, instance=user, partial=True)
                for field, value in data.items():
                    setattr(user, field, value)
                if 'phone' in data:
                    user.phone_verified = False
                user.save()
        except IntegrityError:
            raise ValidationError({'username': ['Bu kullanıcı adı kullanılıyor.']})
        return Response({'user': user_data(user)})


class EmailResendView(ProtectedView):
    def post(self, request):
        validated(StrictSerializer, request)
        with transaction.atomic():
            user = locked_user(request)
            if not user.email_verified:
                send_verification(user)
        return Response({'detail': 'Gerekliyse doğrulama bağlantısı gönderildi.'})


class EmailChangeView(ProtectedView):
    def post(self, request):
        recent(request)
        email = validated(EmailInput, request)['email']
        with transaction.atomic():
            user = locked_user(request, sensitive=True)
            if User.objects.filter(email=email).exists():
                raise ValidationError({'email': ['Bu e-posta kullanılıyor.']})
            if not security.reserve_verification_email(email):
                raise RateLimited()
            nonce = secrets.token_hex(16)
            payload = {'user_id': user.pk, 'email': user.email, 'new_email': email,
                       'security_version': user.security_version, 'purpose': 'change', 'nonce': nonce}
            token = security.issue_token('email-verify', payload, 86400)
            link = settings.FRONTEND_ORIGIN + '/eposta-dogrula?' + urlencode({'key': token})
            try:
                delivery('FIRST yeni e-posta doğrulama', 'Yeni adresinizi onaylamak için bağlantıyı açıp formu gönderin.\n'
                         'Bağlantı 24 saat geçerlidir.\n' + link, email)
                delivery('FIRST e-posta değişikliği bildirimi',
                         'Hesabınız için e-posta değişikliği istendi. Yeni adres doğrulanana kadar bu adres geçerlidir.\n'
                         'Bu işlemi siz başlatmadıysanız şifrenizi sıfırlayın.', user.email)
            except ServiceError:
                security.execute('delete', security.key('email-verify', token))
                raise
            user.email_change_nonce = nonce
            user.save(update_fields=['email_change_nonce'])
        return Response({'detail': 'Yeni adrese doğrulama bağlantısı ve eski adrese bildirim gönderildi.'})


class EmailVerifyView(AuthView):
    def post(self, request):
        require_token_fields(request.data, 'key')
        token = validated(VerifyInput, request)['key']
        try:
            with transaction.atomic():
                user, payload = token_user('email-verify', token)
                if payload.get('purpose') == 'change':
                    if payload.get('nonce') != user.email_change_nonce:
                        raise InvalidToken()
                    if User.objects.filter(email=payload['new_email']).exclude(pk=user.pk).exists():
                        raise ValidationError({'email': ['Bu e-posta kullanılıyor.']})
                    consume('email-verify', token, payload)
                    user.email = payload['new_email']
                    user.email_verified = True
                    user.save(update_fields=['email', 'email_verified'])
                    revoke_all(user)
                elif payload.get('purpose') == 'registration':
                    consume('email-verify', token, payload)
                    user.email_verified = True
                    user.save(update_fields=['email_verified'])
                else:
                    raise InvalidToken()
        except IntegrityError:
            raise ValidationError({'email': ['Bu e-posta kullanılıyor.']})
        return Response({'detail': 'E-posta adresi doğrulandı.'})


class SessionsView(ProtectedView):
    def get(self, request):
        current = security.digest(request.session.session_key)
        records = SessionRecord.objects.filter(user=request.user, revoked=False,
            expires_at__gt=timezone.now(), security_version=request.user.security_version).order_by('-created_at')
        return Response({'sessions': [{'id': str(r.pk), 'created_at': r.created_at.isoformat(),
            'expires_at': r.expires_at.isoformat(), 'current': r.key_hash == current} for r in records]})


class SessionRevokeView(ProtectedView):
    def delete(self, request, session_id):
        validated(StrictSerializer, request)
        if not SessionRecord.objects.filter(pk=session_id, user=request.user, revoked=False).update(revoked=True):
            raise NotFound('Oturum bulunamadı.')
        return Response({'detail': 'Oturum kapatıldı.'})


class SessionsRevokeView(ProtectedView):
    def post(self, request):
        recent(request)
        validated(StrictSerializer, request)
        with transaction.atomic():
            user = locked_user(request, sensitive=True)
            revoke_all(user)
        return Response({'detail': 'Bütün oturumlar kapatıldı.'})
