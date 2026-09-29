"""Presentation allow-lists. Student email and private repository identities stay private."""
from allauth.socialaccount.models import SocialAccount
from django.utils import timezone
from .models import PortfolioRepository, Certificate


def extension(user):
    return getattr(user, 'profile_extension', None)


def student_status(user, *, owner=False):
    row = extension(user)
    valid = bool(row and row.student_verified_until and row.student_verified_until > timezone.now())
    result = {'verified': valid,
              'verified_at': row.student_verified_at.isoformat() if row and row.student_verified_at else None,
              'expires_at': row.student_verified_until.isoformat() if row and row.student_verified_until else None}
    if owner:
        result['email'] = row.student_email if row else ''
    return result


def github_uid(user):
    return SocialAccount.objects.filter(user=user, provider='github').values_list('uid', flat=True).first() or ''


def portfolio_data(row):
    return {'id': str(row.pk), 'repository_id': row.repository_id,
            'repository_name': row.repository_name, 'repository_url': row.repository_url,
            'title': row.title, 'description': row.description, 'role': row.role,
            'created_at': row.created_at.isoformat()}


def portfolio_rows(user):
    # A replaced/unlinked identity cannot inherit another GitHub user's claims.
    uid = github_uid(user)
    return PortfolioRepository.objects.filter(user=user, github_uid=uid) if uid else PortfolioRepository.objects.none()


def certificate_data(row):
    return {'id': str(row.pk), 'title': row.title, 'filename': row.filename, 'size': row.size,
            'kind': row.kind, 'created_at': row.created_at.isoformat(), 'self_declared': True}


def empty_totals():
    return {'merged_prs': 0, 'commits': 0, 'projects': 0,
            'roles': {'owner': 0, 'contributor': 0, 'teammate': 0}}


STATS_SCOPE = ('Hesap açılışından itibaren GitHub aramasında bulunan birleştirilmiş PR ve ana dal commitleri. '
               'Private veriler seçili GitHub App erişimiyle sınırlıdır. Proje sayısı bulunan katkı repolarıdır; '
               'roller FIRST ilanlarındaki sahiplik ve kabul edilmiş katılımlardır. '
               'GitHub indeks gecikmesi ve sonuç sınırları nedeniyle eksikler olabilir.')


def stats_data(user, *, owner=False):
    row = extension(user)
    matching = bool(row and row.stats_github_uid and row.stats_github_uid == github_uid(user))
    saved = row.contribution_stats if matching else {}
    result = {'since': user.date_joined.isoformat(),
              'updated_at': row.stats_updated_at.isoformat() if matching and row.stats_updated_at else None,
              'public': saved.get('public', empty_totals()),
              'share_private_stats': bool(row and row.share_private_stats),
              'partial': bool(saved.get('partial', False)), 'scope': STATS_SCOPE}
    if owner or result['share_private_stats']:
        result['private'] = saved.get('private', empty_totals())
    return result


def public_extension(user):
    return {'student': student_status(user), 'stats': stats_data(user),
            'portfolio': [portfolio_data(row) for row in portfolio_rows(user)],
            'certificates': [certificate_data(row) for row in Certificate.objects.filter(user=user).defer('content')]}
