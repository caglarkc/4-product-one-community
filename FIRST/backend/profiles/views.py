import base64
import binascii
import calendar
import re
import secrets
from pathlib import PurePath
from urllib.parse import urlencode
from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from accounts import security
from accounts.account_views import (ProtectedView, InvalidToken, locked_user, validated,
                                   token_user, consume, delivery, require_token_fields)
from accounts.community_views import public_throttle
from accounts.models import User, username_key
from accounts.proxy import client_ip
from accounts.serializers import StrictSerializer
from accounts.views import AuthView, RateLimited, ServiceError
from moderation.services import profile_visible
from projects.participation import account_for
from showcase.renderers import render
from . import provider, services
from .models import ProfileExtension, PortfolioRepository, Certificate

MIB = 1024 * 1024
LIMITS = {'files': 10, 'file_bytes': 2 * MIB, 'total_bytes': 20 * MIB,
          'extensions': ['pdf', 'jpg', 'jpeg']}


class StudentInput(StrictSerializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        value = value.strip().lower()
        domain = value.rsplit('@', 1)[-1]
        label = r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?'
        if not re.fullmatch(r'(?:' + label + r'\.)+edu\.tr', domain):
            raise ValidationError('Türkiye üniversitelerine ait .edu.tr uzantılı e-posta girin.')
        return value


class VerifyInput(StrictSerializer):
    key = serializers.CharField(max_length=128)


class SettingsInput(StrictSerializer):
    share_private_stats = serializers.BooleanField()

    def validate(self, attrs):
        if type(self.initial_data.get('share_private_stats')) is not bool:
            raise ValidationError({'share_private_stats': ['Boolean gereklidir.']})
        return attrs


class PortfolioInput(StrictSerializer):
    repository = serializers.CharField(max_length=255)

    def validate_repository(self, value):
        if not provider.REPOSITORY_NAME.fullmatch(value):
            raise ValidationError('Repo adresini sahip/repo biçiminde girin.')
        return value


class CertificateInput(StrictSerializer):
    title = serializers.CharField(max_length=200)
    filename = serializers.CharField(max_length=255)
    content_base64 = serializers.CharField(max_length=4 * ((2 * MIB + 2) // 3), trim_whitespace=False)

    def validate_filename(self, value):
        if (PurePath(value).name != value or '/' in value or '\\' in value
                or any(ord(character) < 32 for character in value)
                or PurePath(value).suffix.lower() not in ('.pdf', '.jpg', '.jpeg')):
            raise ValidationError('PDF veya JPG/JPEG dosyası seçin. PNG desteklenmiyor.')
        return value

    def validate_content_base64(self, value):
        try:
            raw = base64.b64decode(value, validate=True)
        except (ValueError, binascii.Error):
            raise ValidationError('Dosya içeriği geçersiz.') from None
        if not raw or len(raw) > LIMITS['file_bytes']:
            raise ValidationError('Her belge en çok 2 MiB olabilir.')
        return raw

    def validate(self, attrs):
        raw = attrs['content_base64']
        suffix = PurePath(attrs['filename']).suffix.lower()
        if not ((suffix == '.pdf' and raw.startswith(b'%PDF-'))
                or (suffix in ('.jpg', '.jpeg') and raw.startswith(b'\xff\xd8\xff'))):
            raise ValidationError({'filename': ['Dosya uzantısı ile içerik uyuşmuyor. PDF veya JPG seçin.']})
        return attrs


def throttle(request, kind='profile-extension-edit', limit=12):
    if security.count(kind, str(request.user.pk), ttl=60) > limit:
        raise RateLimited()


def owner_extension(user):
    # Every caller holds the account lock first, matching unlink and deletion.
    return ProfileExtension.objects.get_or_create(user=user)[0]


def next_year(moment):
    day = min(moment.day, calendar.monthrange(moment.year + 1, moment.month)[1])
    return moment.replace(year=moment.year + 1, day=day)


class SafeView(AuthView):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Vary'] = 'Authorization, Cookie, Origin'
        return response


class OwnerView(SafeView, ProtectedView):
    pass


class StudentView(OwnerView):
    def get(self, request):
        return Response({'student': services.student_status(request.user, owner=True)})


class StudentRequestView(OwnerView):
    def post(self, request):
        data = validated(StudentInput, request)
        if security.count('student-request-ip', client_ip(request), ttl=3600) > 30:
            raise RateLimited()
        if security.count('student-request-user', str(request.user.pk), ttl=3600) > 5:
            raise RateLimited()
        with transaction.atomic():
            user = locked_user(request)
            if not user.email_verified:
                raise PermissionDenied({'detail': 'Önce hesap e-postanızı doğrulayın.', 'code': 'email_verification_required'})
            if not security.reserve_email_change(user.pk, client_ip(request)):
                raise RateLimited()
            if not security.reserve_verification_email(data['email']):
                raise RateLimited()
            row = owner_extension(user)
            nonce = secrets.token_hex(16)
            token = security.issue_token('student-verify', {'user_id': user.pk, 'email': user.email,
                'security_version': user.security_version, 'student_email': data['email'], 'nonce': nonce}, 86400)
            link = settings.FRONTEND_ORIGIN + '/ogrenci-dogrula?' + urlencode({'key': token})
            try:
                delivery('FIRST öğrenci e-postası onayı',
                    'Üniversite e-postasına erişiminizi onaylamak için bağlantıyı açıp onay formunu gönderin.\n'
                    'Bu işlem aktif öğrencilik belgesini denetlemez. Bağlantı 24 saat geçerlidir; rozet 12 ay geçerlidir.\n' + link,
                    data['email'])
            except ServiceError:
                security.execute('delete', security.key('student-verify', token))
                raise
            row.student_request_nonce = nonce
            row.save(update_fields=['student_request_nonce'])
        return Response({'detail': 'Üniversite e-postanıza onay bağlantısı gönderildi.'})


class StudentVerifyView(SafeView):
    def post(self, request):
        if security.count('student-confirm-ip', client_ip(request), ttl=60) > 30:
            raise RateLimited()
        require_token_fields(request.data, 'key')
        key = validated(VerifyInput, request)['key']
        with transaction.atomic():
            user, payload = token_user('student-verify', key)
            row = owner_extension(user)
            if not payload.get('nonce') or row.student_request_nonce != payload.get('nonce'):
                raise InvalidToken()
            email = StudentInput(data={'email': payload.get('student_email')})
            if not email.is_valid():
                raise InvalidToken()
            consume('student-verify', key, payload)
            now = timezone.now()
            row.student_email = email.validated_data['email']
            row.student_verified_at = now
            row.student_verified_until = next_year(now)
            row.student_request_nonce = ''
            row.save(update_fields=['student_email', 'student_verified_at', 'student_verified_until', 'student_request_nonce'])
            return Response({'student': services.student_status(user), 'detail': 'Öğrenci e-postası 12 ay için onaylandı.'})


class SettingsView(OwnerView):
    def get(self, request):
        row = services.extension(request.user)
        return Response({'settings': {'share_private_stats': bool(row and row.share_private_stats)}})

    def patch(self, request):
        throttle(request)
        data = validated(SettingsInput, request)
        with transaction.atomic():
            user = locked_user(request)
            row = owner_extension(user)
            row.share_private_stats = data['share_private_stats']
            row.save(update_fields=['share_private_stats'])
        return Response({'settings': {'share_private_stats': row.share_private_stats}})


class StatsView(OwnerView):
    def get(self, request):
        return Response({'stats': services.stats_data(request.user, owner=True)})


class StatsRefreshView(OwnerView):
    def post(self, request):
        validated(StrictSerializer, request)
        throttle(request, 'contribution-refresh', 3)
        # Keep the account lock during provider reads so disconnect/delete cannot
        # race with a snapshot created under the old identity or access grant.
        with transaction.atomic():
            user = locked_user(request)
            account = account_for(user)
            uid, version = account.uid, user.security_version
            stats = provider.contribution_statistics(account, user)
            current = locked_user(request)
            if current.security_version != version or account_for(current).uid != uid:
                raise PermissionDenied('GitHub kimliği değişti. Yeniden deneyin.')
            row = owner_extension(current)
            row.contribution_stats = stats
            row.stats_github_uid = uid
            row.stats_updated_at = timezone.now()
            row.save(update_fields=['contribution_stats', 'stats_github_uid', 'stats_updated_at'])
            return Response({'stats': services.stats_data(current, owner=True)})


class PortfolioView(OwnerView):
    def get(self, request):
        return Response({'portfolio': [services.portfolio_data(row) for row in services.portfolio_rows(request.user)]})

    def post(self, request):
        throttle(request)
        data = validated(PortfolioInput, request)
        try:
            with transaction.atomic():
                user = locked_user(request)
                account = account_for(user)
                if PortfolioRepository.objects.filter(user=user).count() >= 20:
                    raise ValidationError('Profil vitrini en çok 20 repo içerebilir. Önce bir repo kaldırın.')
                repository = provider.public_repository(account, data['repository'])
                row = PortfolioRepository.objects.create(user=user, github_uid=account.uid, **repository)
        except IntegrityError:
            raise ValidationError({'repository': ['Bu repo profilinizde zaten var.']}) from None
        return Response({'item': services.portfolio_data(row)}, status=201)


class PortfolioItemView(OwnerView):
    def delete(self, request, item_id):
        validated(StrictSerializer, request)
        throttle(request)
        with transaction.atomic():
            user = locked_user(request)
            get_object_or_404(PortfolioRepository, pk=item_id, user=user).delete()
        return Response({'removed': True})


class CertificatesView(OwnerView):
    def get(self, request):
        rows = Certificate.objects.filter(user=request.user).defer('content')
        return Response({'certificates': [services.certificate_data(row) for row in rows], 'limits': LIMITS})

    def post(self, request):
        throttle(request, 'certificate-upload', 5)
        data = validated(CertificateInput, request)
        with transaction.atomic():
            user = locked_user(request)
            existing = Certificate.objects.filter(user=user)
            raw = data['content_base64']
            if existing.count() >= LIMITS['files'] or sum(existing.values_list('size', flat=True)) + len(raw) > LIMITS['total_bytes']:
                raise ValidationError('En çok 10 belge ve toplam 20 MiB yükleyebilirsiniz. Önce bir belge kaldırın.')
            # Reuse the credential-free Linux sandbox. Only sanitized JPEG pages
            # are persisted; embedded PDF actions, raw files and EXIF stay out.
            content = render(data['filename'], raw)
            row = Certificate.objects.create(user=user, title=data['title'], filename=data['filename'],
                size=len(raw), kind=content['kind'], content=content)
        return Response({'certificate': services.certificate_data(row)}, status=201)


class CertificateView(OwnerView):
    def delete(self, request, certificate_id):
        validated(StrictSerializer, request)
        throttle(request)
        with transaction.atomic():
            user = locked_user(request)
            get_object_or_404(Certificate, pk=certificate_id, user=user).delete()
        return Response({'removed': True})


class CertificatePreviewView(SafeView):
    def get(self, request, certificate_id):
        public_throttle(request)
        row = get_object_or_404(Certificate.objects.select_related('user'), pk=certificate_id, user__is_active=True)
        if not profile_visible(row.user, request.user):
            raise NotFound()
        return Response({'certificate': {**services.certificate_data(row), 'content': row.content}})


class PublicExtensionView(SafeView):
    def get(self, request, username):
        public_throttle(request)
        user = get_object_or_404(User.objects.select_related('profile_extension'),
            username_normalized=username_key(username), is_active=True)
        if not profile_visible(user, request.user):
            raise NotFound()
        return Response(services.public_extension(user))
