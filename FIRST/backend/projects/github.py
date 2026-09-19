"""Selected-repository GitHub App access. Never use the login OAuth token."""
import base64
import json
import re
import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import timedelta
from html import unescape
from urllib.parse import quote
import requests
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException
from .models import GitHubCredential


class GitHubAccessError(APIException):
    status_code = 503
    default_detail = {'detail': 'GitHub repo erişimi doğrulanamadı. Bağlantıyı yenileyin.', 'code': 'github_repository_unavailable'}


def enabled():
    return bool(settings.GITHUB_APP_ENABLED and all(getattr(settings, 'GITHUB_APP_' + key) for key in ('ID', 'SLUG', 'CLIENT_ID', 'CLIENT_SECRET', 'REDIRECT_URI', 'TOKEN_KEY')))


def require_enabled():
    if not enabled():
        raise GitHubAccessError()


def cipher():
    try:
        return Fernet(settings.GITHUB_APP_TOKEN_KEY.encode())
    except (ValueError, TypeError):
        raise GitHubAccessError() from None


def token_request(data):
    try:
        response = requests.post('https://github.com/login/oauth/access_token', data={
            'client_id': settings.GITHUB_APP_CLIENT_ID, 'client_secret': settings.GITHUB_APP_CLIENT_SECRET, **data},
            headers={'Accept': 'application/json'}, timeout=10, allow_redirects=False)
        if response.status_code != 200:
            raise GitHubAccessError()
        result = response.json()
        if (not isinstance(result, dict) or result.get('error') or not isinstance(result.get('token_type'), str) or result['token_type'].lower() != 'bearer'
                or not isinstance(result.get('access_token'), str) or not result['access_token']
                or not isinstance(result.get('refresh_token'), str) or not result['refresh_token']
                or type(result.get('expires_in')) is not int or not 60 < result['expires_in'] <= 86400
                or type(result.get('refresh_token_expires_in')) is not int or result['refresh_token_expires_in'] <= 60):
            raise GitHubAccessError()
        return result
    except (requests.RequestException, ValueError, TypeError):
        raise GitHubAccessError() from None


def save_tokens(account, result):
    now = timezone.now()
    return GitHubCredential.objects.update_or_create(account=account, defaults={
        'encrypted_tokens': cipher().encrypt(json.dumps({'access_token': result['access_token'], 'refresh_token': result['refresh_token']}).encode()).decode(),
        'expires_at': now + timedelta(seconds=result['expires_in']),
        'refresh_expires_at': now + timedelta(seconds=result['refresh_token_expires_in'])})[0]


def access_token(account):
    require_enabled()
    # Hold the row lock across refresh and persistence: refresh tokens rotate once.
    with transaction.atomic():
        credential = GitHubCredential.objects.select_for_update().filter(account=account).first()
        if not credential:
            raise GitHubAccessError()
        try:
            tokens = json.loads(cipher().decrypt(credential.encrypted_tokens.encode()))
        except (InvalidToken, ValueError, TypeError):
            raise GitHubAccessError() from None
        if credential.expires_at <= timezone.now() + timedelta(seconds=60):
            if credential.refresh_expires_at <= timezone.now():
                raise GitHubAccessError()
            result = token_request({'grant_type': 'refresh_token', 'refresh_token': tokens['refresh_token']})
            save_tokens(account, result)
            return result['access_token']
        return tokens['access_token']


def revoke_authorization(account):
    """Revoke this user's App grant, never a shared repository installation."""
    token = access_token(account)
    response = None
    try:
        response = requests.delete(
            'https://api.github.com/applications/' + quote(settings.GITHUB_APP_CLIENT_ID, safe='') + '/grant',
            auth=(settings.GITHUB_APP_CLIENT_ID, settings.GITHUB_APP_CLIENT_SECRET),
            json={'access_token': token}, headers={'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'}, timeout=10, allow_redirects=False, stream=True)
        if response.status_code != 204:
            raise GitHubAccessError({'detail': 'GitHub repo izni kaldırılamadı. Bağlantıyı yenileyip tekrar deneyin.',
                                     'code': 'github_revocation_failed'})
    except requests.RequestException:
        raise GitHubAccessError({'detail': 'GitHub şu anda yanıt vermiyor. Uzak izin kaldırma işlemi doğrulanamadı.',
                                 'code': 'github_revocation_failed'}) from None
    finally:
        if response is not None:
            response.close()


_budget = ContextVar('github_request_budget', default=None)


@contextmanager
def request_budget():
    handle = _budget.set({'deadline': time.monotonic() + 22, 'calls': 0})
    try:
        yield
    finally:
        _budget.reset(handle)


def api(token, path, params=None, allow_missing=False):
    budget = _budget.get()
    deadline = min(time.monotonic() + 5, budget['deadline']) if budget else time.monotonic() + 5
    remaining = 5
    if budget is not None:
        budget['calls'] += 1
        remaining = min(5, budget['deadline'] - time.monotonic())
        if budget['calls'] > 12 or remaining <= 0:
            raise GitHubAccessError()
    response = None
    try:
        response = requests.get('https://api.github.com' + path, headers={
            'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'}, params=params, timeout=remaining, allow_redirects=False, stream=True)
        if allow_missing and response.status_code == 404:
            return None
        if response.status_code != 200:
            raise GitHubAccessError()
        # Bound the actual bytes received, not provider-declared README size.
        chunks = bytearray()
        for chunk in response.iter_content(chunk_size=16384):
            chunks.extend(chunk)
            if len(chunks) > 2_000_000 or time.monotonic() >= deadline:
                raise GitHubAccessError()
        result = json.loads(chunks)
        if not isinstance(result, dict):
            raise GitHubAccessError()
        return result
    except (requests.RequestException, ValueError, TypeError):
        raise GitHubAccessError() from None
    finally:
        if response is not None:
            response.close()


def collection(token, path, key, target_id=None):
    rows = []
    for page in range(1, 21):
        data = api(token, path, {'per_page': 100, 'page': page})
        batch = data.get(key)
        if not isinstance(batch, list) or any(not isinstance(row, dict) for row in batch):
            raise GitHubAccessError()
        rows.extend(batch)
        if target_id is not None:
            found = next((row for row in batch if row.get('id') == target_id), None)
            if found is not None:
                return [found]
        total = data.get('total_count')
        if type(total) is int and total >= 0 and len(rows) >= total:
            return rows
        if len(batch) < 100:
            return rows
    raise GitHubAccessError({'detail': 'GitHub repo listesi sınırı aşıldı; daha az repo seçin.', 'code': 'repository_limit'})


def _authorized_repositories(account, installation_id=None, repository_id=None):
    token = access_token(account)
    identity = api(token, '/user')
    if type(identity.get('id')) is not int or str(identity['id']) != account.uid:
        raise GitHubAccessError()
    repositories = []
    installations = collection(token, '/user/installations', 'installations', target_id=installation_id)
    for installation in installations:
        if installation_id is not None and installation.get('id') != installation_id:
            continue
        if str(installation.get('app_id')) != str(settings.GITHUB_APP_ID) or installation.get('suspended_at'):
            continue
        iid = installation.get('id')
        if type(iid) is not int or iid <= 0:
            raise GitHubAccessError()
        for repo in collection(token, f'/user/installations/{iid}/repositories', 'repositories', target_id=repository_id):
            permissions = repo.get('permissions')
            if not isinstance(permissions, dict) or permissions.get('admin') is not True:
                continue
            full_name = repo.get('full_name', '')
            if (type(repo.get('id')) is not int or repo['id'] <= 0 or type(repo.get('private')) is not bool
                    or not isinstance(full_name, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', full_name)):
                raise GitHubAccessError()
            repositories.append({'id': repo['id'], 'installation_id': iid, 'full_name': full_name,
                'name': full_name.split('/')[1], 'private': repo['private'],
                'description': str(repo.get('description') or '')[:1000], 'html_url': 'https://github.com/' + full_name})
    return token, repositories


def authorized_repositories(account):
    with request_budget():
        return _authorized_repositories(account)


def repository(account, installation_id, repository_id):
    with request_budget():
        token, repositories = _authorized_repositories(account, installation_id, repository_id)
    match = next((repo for repo in repositories if repo['id'] == repository_id and repo['installation_id'] == installation_id), None)
    if not match:
        raise GitHubAccessError({'detail': 'Bu repo için seçili kurulum ve yönetici yetkisi gerekiyor.', 'code': 'repository_not_authorized'})
    return token, match


def excerpt(text):
    # Plain, bounded prose only: discard code, images, HTML and link targets.
    text = unescape(text)
    text = re.sub(r'```[\s\S]*?(?:```|$)|~~~[\s\S]*?(?:~~~|$)', ' ', text)
    text = re.sub(r'^(?: {4}|\t).*$', ' ', text, flags=re.M)
    text = re.sub(r'<(script|style)\b[^>]*>[\s\S]*?</\1>', ' ', text, flags=re.I)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)|!\[[^\]]*\]\[[^\]]*\]', ' ', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\[[^\]]*\]', r'\1', text)
    text = re.sub(r'^\s*\[[^\]]+\]:.*$', ' ', text, flags=re.M)
    text = re.sub(r'<[^>]*>|`[^`]*`|https?://\S+', ' ', text)
    text = re.sub(r'^[ \t]*(?:#{1,6}|>|[-*+] |\d+\. )', '', text, flags=re.M)
    text = ' '.join(text.replace('*', '').replace('_', ' ').split())
    return ' '.join(re.split(r'(?<=[.!?])\s+', text)[:3])[:600]


def readme(token, repo):
    data = api(token, '/repos/' + quote(repo['full_name'], safe='/') + '/readme', allow_missing=True)
    if data is None:
        return ''
    content = data.get('content', '')
    if data.get('encoding') != 'base64' or type(data.get('size')) is not int or data['size'] > 262144 or not isinstance(content, str) or len(content) > 360000:
        return ''
    try:
        raw = base64.b64decode(content, validate=False)
        if len(raw) > 262144:
            return ''
        return excerpt(raw.decode('utf-8', errors='replace'))
    except (ValueError, TypeError):
        raise GitHubAccessError() from None
