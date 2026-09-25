"""Explicit, recently authenticated account and repository disconnection."""
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import logout
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from accounts import security
from accounts.account_views import ProtectedView, locked_user, validated
from accounts.models import SessionRecord
from accounts.serializers import StrictSerializer, user_data
from projects import github
from projects.models import GitHubCredential, Project


class ConfirmationInput(StrictSerializer):
    confirmation = serializers.CharField(max_length=32, trim_whitespace=False)


def confirm(request, expected):
    if validated(ConfirmationInput, request)['confirmation'] != expected:
        raise serializers.ValidationError({'confirmation': ['İşlem onayı eşleşmiyor.']})


def disconnect_repositories(user):
    account = SocialAccount.objects.filter(user=user, provider='github').first()
    revoked = None
    if account and GitHubCredential.objects.filter(account=account).exists():
        try:
            github.revoke_authorization(account)
            revoked = True
        except github.GitHubAccessError:
            # Local deletion remains available even for expired/revoked credentials.
            revoked = False
        GitHubCredential.objects.filter(account=account).delete()
    archived = Project.objects.filter(owner=user, is_active=True).update(is_active=False)
    return archived, {'github_authorization_revoked': revoked, 'github_cleanup_required': revoked is False}


def result(detail, cleanup, **extra):
    if cleanup['github_cleanup_required']:
        detail += ' GitHub yetkisi uzaktan kaldırılamadı; GitHub ayarlarından uygulama iznini ayrıca kaldırın.'
    return Response({'detail': detail, **cleanup, **extra})


def invalidate_other_sessions(request, user):
    """Invalidate pending OAuth/recovery flows while retaining this authenticated session."""
    user.security_version += 1
    user.email_change_nonce = ''
    user.save(update_fields=['security_version', 'email_change_nonce'])
    current = security.digest(request.session.session_key)
    SessionRecord.objects.filter(user=user).exclude(key_hash=current).update(revoked=True)
    SessionRecord.objects.filter(user=user, key_hash=current).update(security_version=user.security_version)
    for key in ('github_binder', 'github_app_binder', 'google_binder', 'github_signup', 'google_signup'):
        request.session.pop(key, None)


class GitHubDisconnectView(ProtectedView):
    def post(self, request):
        confirm(request, 'GITHUB')
        with transaction.atomic():
            user = locked_user(request, sensitive=True)
            accounts = SocialAccount.objects.filter(user=user)
            if accounts.filter(provider='github').exists() and not user.has_usable_password() and not accounts.exclude(provider='github').exists():
                raise PermissionDenied({'detail': 'GitHub tek giriş yönteminiz. Önce e-posta üzerinden şifre oluşturun veya FIRST hesabınızı silin.', 'code': 'last_login_method'})
            archived, cleanup = disconnect_repositories(user)
            accounts.filter(provider='github').delete()
            invalidate_other_sessions(request, user)
        return result('GitHub hesap bağlantısı ve FIRST repo erişimi kaldırıldı. Aktif paylaşımlar arşivlendi.',
                      cleanup, user=user_data(user), archived_projects=archived)


class RepositoryDisconnectView(ProtectedView):
    def post(self, request):
        confirm(request, 'REPO')
        with transaction.atomic():
            user = locked_user(request, sensitive=True)
            archived, cleanup = disconnect_repositories(user)
            invalidate_other_sessions(request, user)
        return result('FIRST repo erişimi kaldırıldı. Aktif paylaşımlar arşivlendi; GitHub giriş bağlantınız korundu.',
                      cleanup, user=user_data(user), archived_projects=archived)


class AccountDeleteView(ProtectedView):
    def delete(self, request):
        confirm(request, 'HESABIMI SIL')
        with transaction.atomic():
            user = locked_user(request, sensitive=True)
            from teams.services import assert_account_deletable
            assert_account_deletable(user)
            _, cleanup = disconnect_repositories(user)
            user.delete()
        logout(request)
        return result('FIRST hesabınız ve paylaşımlarınız silindi. Tüm FIRST oturumlarınız kapatıldı.', cleanup)
