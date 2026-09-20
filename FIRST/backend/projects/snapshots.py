"""Owner-scoped repository imports and exact, single-use publication previews."""
import uuid
from allauth.socialaccount.models import SocialAccount
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied
from accounts.account_views import locked_user
from . import github
from .models import GitHubCredential, PreparedRepository, RepositoryCache


class SnapshotChanged(APIException):
    status_code = 409
    default_detail = {'detail': 'Repo bilgileri veya bağlantınız değişti. Listeyi yeniden açıp paylaşımı tekrar hazırlayın.',
                      'code': 'repository_snapshot_changed'}


def connection(request, eligible=False, expected=None):
    """Caller owns an atomic transaction; all writes lock user, then credential."""
    user = locked_user(request)
    if eligible and not user.email_verified:
        raise PermissionDenied({'detail': 'Önce e-posta adresinizi doğrulayın.', 'code': 'email_verification_required'})
    account = SocialAccount.objects.filter(user=user, provider='github').first()
    if not account:
        raise PermissionDenied({'detail': 'Önce GitHub hesabınızı bağlayın.', 'code': 'github_link_required'})
    credential = GitHubCredential.objects.select_for_update().filter(account=account).first()
    if not credential:
        raise SnapshotChanged()
    if expected is not None and (account.pk, account.uid, credential.pk) != expected:
        raise SnapshotChanged()
    return user, account, credential


def current_cache(credential, cache_id, generation):
    cache = RepositoryCache.objects.filter(pk=cache_id, credential=credential, generation=generation).first()
    if not cache:
        raise SnapshotChanged()
    return cache


def cache_data(cache):
    return {'repositories': cache.repositories, 'cached_at': cache.cached_at.isoformat() if cache.cached_at else None}


def repositories(request, refresh=False):
    with transaction.atomic():
        _, account, credential = connection(request)
        cache, _ = RepositoryCache.objects.get_or_create(credential=credential)
        if not refresh and cache.cached_at is not None:
            return cache_data(cache)
        # Reserve this fetch; a later explicit refresh supersedes older work.
        cache.generation = uuid.uuid4()
        cache.save(update_fields=['generation'])
        expected = (account.pk, account.uid, credential.pk)
        cache_id, generation = cache.pk, cache.generation
    # Network errors leave the last successful list, including an empty list,
    # intact. Never hold the user's database lock across provider requests.
    _, rows = github.authorized_repositories(account)
    with transaction.atomic():
        _, _, credential = connection(request, expected=expected)
        cache = current_cache(credential, cache_id, generation)
        cache.repositories = rows
        cache.cached_at = timezone.now()
        # Also invalidate preview work begun while this refresh was in flight.
        cache.generation = uuid.uuid4()
        cache.save(update_fields=['repositories', 'cached_at', 'generation'])
        PreparedRepository.objects.filter(credential=credential).delete()
        return cache_data(cache)


def prepare(request, selection):
    with transaction.atomic():
        _, account, credential = connection(request, eligible=True)
        cache = RepositoryCache.objects.filter(credential=credential, cached_at__isnull=False).first()
        if not cache:
            raise SnapshotChanged()
        repo = next((row for row in cache.repositories
                     if row['installation_id'] == selection['installation_id']
                     and row['id'] == selection['repository_id']), None)
        if not repo:
            raise SnapshotChanged()
        expected = (account.pk, account.uid, credential.pk)
        cache_id, generation = cache.pk, cache.generation
    # Only README is imported on explicit preparation; repository metadata
    # comes from the owner's stored selection, never another enumeration.
    token = github.access_token(account)
    excerpt = github.readme(token, repo)
    with transaction.atomic():
        _, _, credential = connection(request, eligible=True, expected=expected)
        current_cache(credential, cache_id, generation)
        preview, _ = PreparedRepository.objects.update_or_create(credential=credential, **selection,
            defaults={'preview_token': uuid.uuid4(), 'cache_generation': generation,
                      'repository': repo, 'readme_excerpt': excerpt})
        return {'repository': repo, 'readme_excerpt': excerpt, 'preview_token': str(preview.preview_token)}
