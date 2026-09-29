"""Manual, bounded GitHub reads. Login OAuth secrets are never needed or persisted."""
import re
from datetime import timedelta
from urllib.parse import quote
from django.utils import timezone
from projects import github, github_participation as provider
from projects.models import Project, Participation
from .services import empty_totals

REPOSITORY_NAME = re.compile(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+')


def object_value(value):
    if not isinstance(value, dict):
        raise github.GitHubAccessError()
    return value


def identity(token, account):
    data = object_value(provider._api(token, '/user'))
    login = data.get('login')
    if (account.provider != 'github' or str(data.get('id')) != str(account.uid)
            or not isinstance(login, str) or not re.fullmatch(r'[A-Za-z0-9-]{1,39}', login)):
        raise github.GitHubAccessError({'detail': 'GitHub kimliği değişti. Bağlantınızı yenileyin.',
                                      'code': 'github_identity_mismatch'})
    return login


def search(token, path, query, *, size=100):
    result = object_value(provider._api(token, path, params={'q': query, 'per_page': size, 'page': 1}))
    total, items = result.get('total_count'), result.get('items')
    if type(total) is not int or total < 0 or not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise github.GitHubAccessError()
    return total, items, bool(result.get('incomplete_results', True) or total > len(items))


def public_repository(account, name):
    # Anonymous retrieval proves this exact metadata is public at import time.
    with provider.operation_budget():
        repo = object_value(provider._api(None, '/repos/' + quote(name, safe='/')))
        rid, full_name = repo.get('id'), repo.get('full_name')
        if (type(rid) is not int or rid <= 0 or repo.get('private') is not False
                or not isinstance(full_name, str) or not REPOSITORY_NAME.fullmatch(full_name)
                or repo.get('disabled')):
            raise github.GitHubAccessError({'detail': 'Vitrine yalnız herkese açık GitHub repoları eklenebilir.',
                                          'code': 'portfolio_public_required'})
        role = 'owner' if str(object_value(repo.get('owner')).get('id')) == str(account.uid) else ''
        if not role and Participation.objects.filter(user_id=account.user_id, github_uid=account.uid,
                status='accepted', project__repository_id=rid).exists():
            role = 'contributor'
        if not role:
            # Public GitHub accepted contributions can predate FIRST. Only stats,
            # rather than eligibility for a portfolio, start at the signup date.
            identity_data = object_value(provider._api(None, '/user/' + quote(str(account.uid), safe='')))
            login = identity_data.get('login')
            if str(identity_data.get('id')) != str(account.uid) or not isinstance(login, str) or not re.fullmatch(r'[A-Za-z0-9-]{1,39}', login):
                raise github.GitHubAccessError()
            total, rows, _ = search(None, '/search/issues',
                f'repo:{full_name} author:{login} is:pr is:merged is:public', size=1)
            if total and rows and str(object_value(rows[0].get('user')).get('id')) == str(account.uid):
                number = rows[0].get('number')
                if type(number) is not int or number <= 0:
                    raise github.GitHubAccessError()
                pull = object_value(provider._api(None, '/repos/' + quote(full_name, safe='/') + '/pulls/' + str(number)))
                if (pull.get('merged') is True and str(object_value(pull.get('user')).get('id')) == str(account.uid)
                        and object_value(object_value(pull.get('base')).get('repo')).get('id') == rid):
                    role = 'contributor'
        if not role:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'repository': ['Repo sahibi veya kabul edilmiş katkıcısı olmalısınız.']})
        return {'repository_id': rid, 'repository_name': full_name,
                'repository_url': 'https://github.com/' + full_name, 'title': full_name.split('/')[-1][:200],
                'description': str(repo.get('description') or '')[:1000], 'role': role}


def contribution_statistics(account, user):
    # The date-time qualifier avoids importing contributions earlier on signup day.
    # GitHub exposes second precision. Round up a fractional signup second so
    # a provider timestamp earlier than the exact account creation is excluded.
    start = user.date_joined
    if start.microsecond:
        start += timedelta(seconds=1)
    since = start.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    until = timezone.now().replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    output = {'public': empty_totals(), 'private': empty_totals(), 'partial': False}
    with provider.operation_budget():
        token = github.access_token(account)
        login = identity(token, account)
        for visibility in ('public', 'private'):
            totals, repositories = output[visibility], set()
            for metric, path, term in [('merged_prs', '/search/issues', f'is:pr is:merged merged:{since}..{until}'),
                                       ('commits', '/search/commits', f'author-date:{since}..{until}')]:
                count, rows, partial = search(token, path, f'author:{login} is:{visibility} {term}')
                totals[metric] = count
                output['partial'] |= partial
                for row in rows:
                    if metric == 'commits':
                        repo = object_value(row.get('repository'))
                        name = repo.get('full_name')
                        if not isinstance(name, str) or not REPOSITORY_NAME.fullmatch(name):
                            raise github.GitHubAccessError()
                    else:
                        url = row.get('repository_url', '')
                        if not isinstance(url, str) or not url.startswith('https://api.github.com/repos/'):
                            raise github.GitHubAccessError()
                        name = url.removeprefix('https://api.github.com/repos/')
                        if not REPOSITORY_NAME.fullmatch(name):
                            raise github.GitHubAccessError()
                    repositories.add(name.lower())
            totals['projects'] = len(repositories)
            private = visibility == 'private'
            totals['roles']['owner'] = Project.objects.filter(owner=user, is_private=private,
                                                              created_at__gte=user.date_joined).values('repository_id').distinct().count()
            accepted = Participation.objects.filter(user=user, github_uid=account.uid, status='accepted',
                updated_at__gte=user.date_joined, project__is_private=private)
            totals['roles']['teammate'] = accepted.filter(project__need_type='teammate').values('project__repository_id').distinct().count()
            totals['roles']['contributor'] = accepted.exclude(project__need_type='teammate').values('project__repository_id').distinct().count()
    # Only aggregate numbers cross the persistence boundary, never repository names.
    return output
