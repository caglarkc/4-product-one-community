"""Bounded GitHub App operations for listings; login OAuth tokens are never used.

Automatic invitations accept only a deliberately narrow, provable ruleset policy.
No GitHub settings or App permissions are changed by this module.
"""
import json
import re
import time
from contextvars import ContextVar
from contextlib import contextmanager
from functools import wraps
from urllib.parse import quote

import requests
from . import github

_budget = ContextVar('participation_github_budget', default=None)


def _error(code='github_participation_unavailable', message='GitHub işlemi doğrulanamadı. Repo izinlerini kontrol edip yeniden deneyin.'):
    raise github.GitHubAccessError({'detail': message, 'code': code})


@contextmanager
def operation_budget():
    """Share one deadline across merge plus invitation and other multi-step work."""
    if _budget.get() is not None:
        yield
        return
    handle = _budget.set({'deadline': time.monotonic() + 20, 'calls': 0})
    try:
        yield
    finally:
        _budget.reset(handle)


def bounded(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with operation_budget():
            return fn(*args, **kwargs)
    return wrapper


def _api(token, path, *, method='GET', data=None, params=None, missing=False):
    if not path.startswith('/') or path.startswith('//') or '?' in path or '#' in path:
        _error()
    budget = _budget.get()
    budget['calls'] += 1
    remaining = min(4, budget['deadline'] - time.monotonic())
    if budget['calls'] > 35 or remaining <= 0:
        _error('github_request_limit')
    response = None
    try:
        response = requests.request(method, 'https://api.github.com' + path, headers={
            **({'Authorization': 'Bearer ' + token} if token else {}), 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'}, json=data, params=params,
            timeout=remaining, allow_redirects=False, stream=True)
        if missing and response.status_code == 404:
            return None
        if response.status_code not in (200, 201, 204):
            _error('github_permission_or_operation_failed',
                   'GitHub işlemi tamamlanamadı. Uygulamanın repo izinlerini ve işlemin güncel durumunu kontrol edin.')
        if response.status_code == 204:
            return {}
        payload = bytearray()
        # Check the deadline between bytes so a trickling body cannot hold a
        # large buffered chunk open indefinitely past the operation budget.
        for chunk in response.iter_content(1):
            payload.extend(chunk)
            if len(payload) > 2_000_000 or time.monotonic() > budget['deadline']:
                _error('github_response_limit')
        result = json.loads(payload)
        if not isinstance(result, (dict, list)):
            _error()
        return result
    except (requests.RequestException, ValueError, TypeError):
        _error()
    finally:
        if response is not None:
            response.close()


def _list(token, path, params=None):
    result = []
    for page in range(1, 11):
        rows = _api(token, path, params={**(params or {}), 'page': page, 'per_page': 100})
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            _error()
        result.extend(rows)
        if len(rows) < 100:
            return result
    _error('github_collection_limit', 'GitHub liste sınırı aşıldı; işlem güvenle doğrulanamadı.')


def _dict(value):
    if not isinstance(value, dict):
        _error()
    return value


def _number(value):
    if type(value) is not int or value <= 0:
        _error()
    return value


def _owner(account, project):
    # User access tokens intersect the current App grant with this user's rights.
    # Numeric lookup avoids stale names/transfers and costly installation enumeration.
    token = github.access_token(account)
    identity = _dict(_api(token, '/user'))
    if account.provider != 'github' or str(identity.get('id')) != str(account.uid):
        _error('github_identity_mismatch')
    repo = _dict(_api(token, '/repositories/' + str(_number(project.repository_id))))
    full_name = repo.get('full_name')
    if (repo.get('id') != project.repository_id or type(repo.get('id')) is not int
            or _dict(repo.get('permissions')).get('admin') is not True
            or not isinstance(full_name, str)
            or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', full_name)
            or type(repo.get('private')) is not bool or repo.get('archived') or repo.get('disabled')):
        _error('repository_not_authorized')
    return token, '/repos/' + quote(full_name, safe='/'), repo


def _read_token(repo, project, reader_account):
    # Public data is fetched anonymously: a concurrent privacy change then makes
    # the actual content request fail instead of borrowing the owner's access.
    if not repo['private']:
        return None
    if reader_account is None:
        _error('github_repository_read_required', 'Private repo bilgileri için güncel GitHub repo erişimi gerekir.')
    token = github.access_token(reader_account)
    identity = _dict(_api(token, '/user'))
    if reader_account.provider != 'github' or str(identity.get('id')) != str(reader_account.uid):
        _error('github_identity_mismatch')
    # Actual Issue/PR reads use this token, so GitHub enforces access at retrieval.
    return token


@bounded
def repository_access(owner_account, project, reader_account=None):
    _, _, repo = _owner(owner_account, project)
    allowed = not repo['private'] or (reader_account is not None and can_read_repository(reader_account, project))
    return {'private': repo['private'], 'can_read': allowed}


def _target(token, account):
    uid = str(account.uid)
    if account.provider != 'github' or not re.fullmatch(r'[1-9][0-9]{0,19}', uid):
        _error('github_identity_mismatch')
    user = _dict(_api(token, '/user/' + uid))
    login = user.get('login')
    if str(user.get('id')) != uid or not isinstance(login, str) or not re.fullmatch(r'[A-Za-z0-9-]{1,39}', login):
        _error('github_identity_mismatch')
    # Pin the mutable login to its stable numeric identity immediately before use.
    current = _dict(_api(token, '/users/' + quote(login, safe='')))
    if current.get('id') != user.get('id'):
        _error('github_identity_mismatch')
    return user


@bounded
def can_read_repository(account, project):
    token = github.access_token(account)
    identity = _dict(_api(token, '/user'))
    if str(identity.get('id')) != str(account.uid):
        _error('github_identity_mismatch')
    repo = _api(token, '/repositories/' + str(_number(project.repository_id)), missing=True)
    if repo is None:
        return False
    repo = _dict(repo)
    if type(repo.get('id')) is not int or repo.get('id') != project.repository_id:
        return False
    # GitHub user tokens intersect user permissions with the installed App grant.
    return repo.get('private') is False or _dict(repo.get('permissions')).get('pull') is True


def _issue_data(item, repo):
    item = _dict(item)
    number = _number(item.get('number'))
    if 'pull_request' in item:
        _error('github_issue_required', 'Bir pull request yerine GitHub Issue seçin.')
    return {'id': _number(item.get('id')), 'number': number, 'title': str(item.get('title', ''))[:256],
            'state': item.get('state'), 'url': 'https://github.com/' + repo['full_name'] + '/issues/' + str(number)}


@bounded
def issues(owner_account, project, reader_account=None):
    token, path, repo = _owner(owner_account, project)
    token = _read_token(repo, project, reader_account)
    return [_issue_data(row, repo) for row in _list(token, path + '/issues', {'state': 'open'}) if 'pull_request' not in row]


@bounded
def issue(owner_account, project, number, reader_account=None):
    token, path, repo = _owner(owner_account, project)
    token = _read_token(repo, project, reader_account)
    return _issue_data(_api(token, path + '/issues/' + str(_number(number))), repo)


@bounded
def create_issue(owner_account, project, title, body, operation_key):
    token, path, repo = _owner(owner_account, project)
    if not isinstance(operation_key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', operation_key):
        _error('github_operation_key_invalid')
    marker = '<!-- FIRST issue operation: ' + operation_key + ' -->'
    for row in _list(token, path + '/issues', {'state': 'all', 'sort': 'created', 'direction': 'desc'}):
        if 'pull_request' not in row and marker in str(row.get('body') or ''):
            if str(_dict(row.get('user')).get('id')) != str(owner_account.uid):
                _error('github_issue_operation_identity_changed',
                       'Bu Issue işlemi başka GitHub kimliğiyle eşleşiyor. Yeni Issue oluşturmadan mevcut işlemi kontrol edin.')
            return _issue_data(row, repo)
    if not isinstance(title, str) or not title.strip() or len(title) > 200 or not isinstance(body, str) or len(body) > 20000:
        _error('github_issue_invalid')
    return _issue_data(_api(token, path + '/issues', method='POST', data={'title': title, 'body': body + '\n\n' + marker}), repo)


def _pull_data(item, repo, applicant=None):
    item = _dict(item)
    if _dict(_dict(item.get('base')).get('repo')).get('id') != repo['id']:
        _error('github_pull_repository_mismatch')
    if applicant is not None and str(_dict(item.get('user')).get('id')) != str(applicant.uid):
        _error('github_pull_author_mismatch', 'PR bağlı GitHub hesabınıza ait olmalıdır.')
    sha = _dict(item.get('head')).get('sha')
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{40,64}', sha):
        _error()
    number = _number(item.get('number'))
    return {'id': _number(item.get('id')), 'number': number, 'sha': sha,
            'url': 'https://github.com/' + repo['full_name'] + '/pull/' + str(number),
            'title': str(item.get('title', ''))[:256], 'state': item.get('state'),
            'merged': item.get('merged') is True or bool(item.get('merged_at')),
            'draft': item.get('draft') is True, 'author_uid': str(_dict(item.get('user')).get('id'))}


@bounded
def pull_requests(owner_account, project, reader_account=None):
    token, path, repo = _owner(owner_account, project)
    token = _read_token(repo, project, reader_account)
    return [_pull_data(row, repo) for row in _list(token, path + '/pulls', {'state': 'open'})]


@bounded
def check_pull_request(owner_account, project, number, applicant_account):
    token, path, repo = _owner(owner_account, project)
    if repo['private']:
        _error('github_public_pull_required', 'PR ile katılım yalnız güncel olarak public repolarda kullanılabilir.')
    pr = _pull_data(_api(None, path + '/pulls/' + str(_number(number))), repo, applicant_account)
    if pr['state'] != 'open' or pr['draft'] or pr['merged']:
        _error('github_pull_not_open', 'Başvuru için açık ve taslak olmayan bir PR gerekir.')
    return pr


@bounded
def merge_pull_request(owner_account, project, number, applicant_account, expected_sha):
    token, path, repo = _owner(owner_account, project)
    pr_path = path + '/pulls/' + str(_number(number))
    pr = _pull_data(_api(token, pr_path), repo, applicant_account)
    if pr['sha'] != expected_sha:
        _error('github_pull_changed', 'PR değişti. Güncel değişiklikleri inceleyip yeniden deneyin.')
    if pr['merged']:
        return pr
    if pr['state'] != 'open' or pr['draft']:
        _error('github_pull_not_mergeable', 'Yalnız açık ve taslak olmayan PR kabul edilebilir.')
    result = _dict(_api(token, pr_path + '/merge', method='PUT', data={'sha': expected_sha, 'merge_method': 'merge'}))
    if result.get('merged') is not True:
        _error('github_pull_not_merged')
    return {**pr, 'merged': True, 'state': 'closed'}


def _safe_ruleset(row, repo):
    if row.get('enforcement') != 'active' or row.get('target') not in ('branch', 'tag'):
        return False
    actors = row.get('bypass_actors')
    if not isinstance(actors, list):
        return False  # Absent bypass data is not proof of absence.
    for actor in actors:
        if not isinstance(actor, dict):
            return False
        # GitHub built-in RepositoryRole 5 is repository admin. Never accept write/maintain or integrations.
        if not ((actor.get('actor_type') == 'RepositoryRole' and actor.get('actor_id') == 5)
                or (actor.get('actor_type') == 'OrganizationAdmin' and _dict(repo.get('owner')).get('type') == 'Organization')
                or (actor.get('actor_type') == 'User' and actor.get('actor_id') == _dict(repo.get('owner')).get('id'))):
            return False
    rules = row.get('rules')
    if not isinstance(rules, list) or any(not isinstance(rule, dict) for rule in rules):
        return False
    types = {rule.get('type') for rule in rules}
    if not {'update', 'deletion', 'non_fast_forward'}.issubset(types):
        return False
    return not any(rule.get('type') == 'update' and _dict(rule.get('parameters', {})).get('update_allows_fetch_and_merge') is True for rule in rules)


def _covers(row, ref, default_branch):
    condition = _dict(_dict(row.get('conditions')).get('ref_name'))
    include, exclude = condition.get('include'), condition.get('exclude')
    # Avoid approximating GitHub's fnmatch engine: only exact refs and built-in selectors are accepted.
    if not isinstance(include, list) or exclude != []:
        return False
    return '~ALL' in include or ref in include or (ref == 'refs/heads/' + default_branch and '~DEFAULT_BRANCH' in include)


def _safety(token, path, repo):
    # A configured ruleset is insufficient on a private repository whose plan
    # does not enforce it. Missing plan metadata deliberately fails closed.
    if repo['private']:
        owner = _dict(repo.get('owner'))
        if owner.get('type') == 'Organization':
            account = _dict(_api(token, '/orgs/' + quote(str(owner.get('login', '')), safe='')))
            supported = {'team', 'enterprise', 'enterprise_cloud'}
        else:
            account = _dict(_api(token, '/user'))
            if account.get('id') != owner.get('id'):
                _error('github_protection_required', 'Private repo için sahibinin koruma destekli GitHub planı doğrulanmalıdır.')
            supported = {'pro'}
        plan = account.get('plan')
        if not isinstance(plan, dict) or str(plan.get('name', '')).lower() not in supported:
            _error('github_protection_required', 'Private repo için etkin kural desteği olan GitHub Pro/Team/Enterprise planı doğrulanamadı.')
    details = []
    for row in _list(token, path + '/rulesets', {'includes_parents': 'false'}):
        ruleset = _dict(_api(token, path + '/rulesets/' + str(_number(row.get('id')))))
        if _safe_ruleset(ruleset, repo):
            details.append(ruleset)
    branches = _list(token, path + '/branches')
    default = repo.get('default_branch')
    if not isinstance(default, str) or not default or not branches:
        _error('github_protection_required', 'Otomatik katılım için doğrulanabilir varsayılan dal ve etkin GitHub kuralları gerekir.')
    names = [row.get('name') for row in branches]
    if default not in names or any(not isinstance(name, str) or not name for name in names):
        _error('github_protection_required')
    for name in names:
        if not any(row['target'] == 'branch' and _covers(row, 'refs/heads/' + name, default) for row in details):
            _error('github_protection_required', 'Otomatik katılım kapalı: mevcut bütün dallar için güncelleme, silme ve force-push kısıtları; yalnız yönetici bypass izni gerekiyor. Yeni çalışma dalları ayrıca açılabilir.')
    if not any(row['target'] == 'tag' and _covers(row, 'refs/tags/FIRST-protection-check', default)
               and '~ALL' in row['conditions']['ref_name']['include'] for row in details):
        _error('github_protection_required', 'Otomatik katılım kapalı: bütün etiketlerde güncelleme, silme ve force-push kısıtları; yalnız yönetici bypass izni gerekiyor.')
    return {'safe': True, 'protected_branch_count': len(names), 'policy': 'existing_branches_and_all_tags_admin_only'}


@bounded
def automatic_access_safety(owner_account, project):
    token, path, repo = _owner(owner_account, project)
    return _safety(token, path, repo)


def _invitation_status(token, path, repo, target):
    permission = _api(token, path + '/collaborators/' + quote(target['login'], safe='') + '/permission', missing=True)
    if permission is not None:
        permission = _dict(permission)
        user = _dict(permission.get('user'))
        if user.get('id') != target['id']:
            _error('github_identity_mismatch')
        if permission.get('permission') in ('write', 'admin', 'maintain') or permission.get('role_name') in ('write', 'admin', 'maintain'):
            return {'status': 'active', 'invitation_id': None, 'url': 'https://github.com/' + repo['full_name'],
                    'access_level': permission.get('role_name') or permission.get('permission'), 'existing_access': True}
    for row in _list(token, path + '/invitations'):
        if (_dict(row.get('invitee')).get('id') == target['id']
                and row.get('permissions') in ('write', 'admin', 'maintain')):
            return {'status': 'invited', 'invitation_id': _number(row.get('id')),
                    'url': 'https://github.com/' + repo['full_name'] + '/invitations'}
    return {'status': 'missing', 'invitation_id': None, 'url': ''}


@bounded
def invitation_status(owner_account, project, applicant_account):
    token, path, repo = _owner(owner_account, project)
    return _invitation_status(token, path, repo, _target(token, applicant_account))


@bounded
def invite_collaborator(owner_account, project, applicant_account, automatic=False):
    token, path, repo = _owner(owner_account, project)
    target = _target(token, applicant_account)
    if automatic:
        _safety(token, path, repo)
    status = _invitation_status(token, path, repo, target)
    if status['status'] in ('active', 'invited'):
        return status
    # Resolve again after potentially lengthy ruleset/invitation reads.
    target = _target(token, applicant_account)
    result = _dict(_api(token, path + '/collaborators/' + quote(target['login'], safe=''),
                        method='PUT', data={'permission': 'push'}))
    if not result:
        reconciled = _invitation_status(token, path, repo, target)
        if reconciled['status'] != 'active':
            _error('github_invitation_unconfirmed')
        return reconciled
    if _dict(result.get('invitee')).get('id') != target['id'] or _dict(result.get('repository')).get('id') != repo['id']:
        _error('github_invitation_identity_mismatch')
    return {'status': 'invited', 'invitation_id': _number(result.get('id')),
            'url': 'https://github.com/' + repo['full_name'] + '/invitations'}
