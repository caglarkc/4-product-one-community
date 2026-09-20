import time
from datetime import timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler
from . import security
from .authentication import DjangoSessionAuthentication
from .models import User, SessionRecord
from .proxy import client_ip
from .serializers import RegisterSerializer, LoginSerializer, StrictSerializer, user_data


class ServiceError(APIException):
    status_code = 503
    default_detail = 'Hizmet geçici olarak kullanılamıyor.'


class RateLimited(APIException):
    status_code = 429
    default_detail = 'Çok fazla deneme. Daha sonra tekrar deneyin.'


def errors(exc, context):
    if isinstance(exc, security.SecurityUnavailable):
        return Response({'detail': 'Kimlik hizmeti geçici olarak kullanılamıyor.', 'code': 'service_unavailable'}, status=503)
    response = exception_handler(exc, context)
    if response is not None and isinstance(exc, ValidationError):
        response.data = {'detail': 'Alanları kontrol edin.', 'errors': response.data}
    return response


def csrf_failure(request, reason=''):
    return JsonResponse({'detail': 'Güvenlik doğrulaması başarısız. Sayfayı yenileyin.', 'code': 'csrf_failed'}, status=403)


@method_decorator(csrf_protect, name='dispatch')
class AuthView(APIView):
    authentication_classes = [DjangoSessionAuthentication]  # Explicit CSRF also protects anonymous POST.
    permission_classes = []

    def user(self, request):
        return request._request.user


class CsrfView(AuthView):
    def get(self, request):
        if not request.session.session_key:
            if security.count('session-bootstrap-ip', client_ip(request), ttl=60) > settings.AUTH_IP_ATTEMPTS:
                raise RateLimited()
            # Fixed expiry bounds abandoned anonymous OAuth/CSRF state.
            request.session.set_expiry(timezone.now() + timedelta(minutes=10))
            request.session.create()
        return Response({'csrfToken': get_token(request._request)})


class ConfigView(AuthView):
    def get(self, request):
        from .google_views import enabled
        from .github_views import enabled as github_enabled
        return Response({'providers': {'google': enabled(), 'github': github_enabled()}, 'phone_verification_available': False})


class MeView(AuthView):
    def get(self, request):
        user = self.user(request)
        return Response({'user': user_data(user) if user.is_authenticated else None})


def start_session(request, user, remember=False, *, password_authenticated=False):
    if request.session.session_key:
        SessionRecord.objects.filter(key_hash=security.digest(request.session.session_key)).update(revoked=True)
    login(request._request, user, backend='django.contrib.auth.backends.ModelBackend')
    request.session.cycle_key()
    duration = 30 * 86400 if remember else 86400
    expires_at = timezone.now() + timedelta(seconds=duration)
    request.session.set_expiry(expires_at)
    # A provider login may reuse an old browser session. Only a password proof
    # grants freshness here; Google reauthentication verifies auth_time itself.
    request.session.pop('reauthenticated_at', None)
    if password_authenticated:
        request.session['reauthenticated_at'] = time.time()
    request.session.save()
    SessionRecord.objects.create(user=user, key_hash=security.digest(request.session.session_key),
        expires_at=expires_at, security_version=user.security_version)


def check_password_proof(request, email, password, user=None):
    """Shared limiter for login, reauthentication and password change."""
    if security.count('password-ip', client_ip(request)) > settings.AUTH_IP_ATTEMPTS:
        raise RateLimited()
    owner = security.acquire_password_lock(email)
    if not owner:
        raise RateLimited()
    try:
        if security.attempts('password-account', email) >= settings.AUTH_ACCOUNT_ATTEMPTS:
            raise RateLimited()
        # Reserve an attempt before expensive hashing: concurrent requests cannot
        # all pass an unchecked failure counter. Success clears the reservation.
        security.count('password-account', email)
        user = user or User.objects.filter(email=email).first()
        valid = bool(user and user.is_active and user.check_password(password))
        if user is None:
            make_password(password)
        if not valid:
            return None
        security.clear('password-account', email)
        return user
    finally:
        security.release_password_lock(email, owner)


def send_verification(user):
    if not security.reserve_verification_email(user.email):
        raise RateLimited()
    token = security.issue_token('email-verify', {'user_id': user.pk, 'email': user.email,
        'security_version': user.security_version, 'purpose': 'registration'}, 86400)
    link = settings.FRONTEND_ORIGIN + '/eposta-dogrula?' + urlencode({'key': token})
    try:
        sent = send_mail('FIRST e-posta doğrulama',
            'E-posta adresinizi doğrulamak için bağlantıyı açın ve onay formunu gönderin.\n'
            'Bağlantı 24 saat geçerlidir.\n' + link,
            settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        if sent != 1:
            raise RuntimeError('Delivery not accepted')
    except Exception as exc:
        security.execute('delete', security.key('email-verify', token))
        raise ServiceError({'detail': 'Doğrulama e-postası gönderilemedi. Yeniden deneyin.', 'code': 'email_delivery_failed'}) from exc
    return token


class RegisterView(AuthView):
    def post(self, request):
        if security.count('register-ip', client_ip(request)) > settings.AUTH_IP_ATTEMPTS:
            raise RateLimited()
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                user = User.objects.create_user(**serializer.validated_data)
                send_verification(user)
                start_session(request, user, password_authenticated=True)
        except IntegrityError:
            raise ValidationError({'non_field_errors': ['E-posta veya kullanıcı adı kullanılıyor.']})
        return Response({'user': user_data(user)}, status=201)


class LoginView(AuthView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = check_password_proof(request, data['email'], data['password'])
        if not user:
            return Response({'detail': 'E-posta veya şifre hatalı.'}, status=400)
        start_session(request, user, data['remember_me'], password_authenticated=True)
        return Response({'user': user_data(user)})


class LogoutView(AuthView):
    def post(self, request):
        serializer = StrictSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            if request.user.is_authenticated:
                # Match the user-first lock order of protected writes and
                # OAuth callback persistence before invalidating the session.
                from .account_views import locked_user
                locked_user(request)
            if request.session.session_key:
                SessionRecord.objects.filter(key_hash=security.digest(request.session.session_key)).update(revoked=True)
            logout(request._request)
        return Response({'detail': 'Oturum kapatıldı.'})
