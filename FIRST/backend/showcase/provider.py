"""Only pinned, regular Git blobs. Never follow GitHub-supplied download URLs."""
import base64
import hashlib
import json
import re
import time
import unicodedata
from urllib.parse import quote
import requests
from urllib3.exceptions import HTTPError
from rest_framework.exceptions import ValidationError
from projects import github_participation as github

MIB = 1024 * 1024
SHA = re.compile(r'^[0-9a-f]{40}$')


def path_value(value, directory=False):
    if directory and value == '':
        return value
    if (not isinstance(value, str) or not value or len(value) > 1024 or len(value.split('/')) > 12
            or any(part in ('', '.', '..') or len(part) > 255 for part in value.split('/'))
            or any(c in value for c in '\\%?#:')
            or any(unicodedata.category(c).startswith('C') for c in value)):
        raise ValidationError({'path': ['Geçersiz dosya yolu.']})
    for part in value.lower().split('/'):
        if (part in {'.git', '.ssh', '.aws', '.npmrc', '.pypirc', '.netrc', 'id_rsa', 'id_ed25519'}
                or part.startswith('.env') or part.endswith(('.pem', '.key', '.p12', '.pfx'))
                or any(word in part for word in ('credential', 'secret', 'token'))):
            raise ValidationError({'path': ['Kimlik bilgisi içerebilecek bu dosya yayımlanamaz.']})
    return value


def _sha(value):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        github._error()
    return value


def authorized(account, project):
    token, root, repo = github._owner(account, project)
    if repo['private'] is not True or not project.is_private:
        raise ValidationError('Dosya vitrini yalnız private repo ilanlarında kullanılabilir.')
    return token, root, repo


def _tree(token, root, sha):
    result = github._dict(github._api(token, root + '/git/trees/' + _sha(sha)))
    rows = result.get('tree')
    if result.get('truncated') is not False or not isinstance(rows, list) or len(rows) > 1000:
        raise ValidationError('Bu dizin liste sınırını aşıyor (en çok 1000 kayıt).')
    if any(not isinstance(row, dict) for row in rows):
        github._error()
    return rows


def directory(token, root, repo, path):
    branch = repo.get('default_branch')
    if not isinstance(branch, str) or not branch:
        github._error()
    commit = github._dict(github._api(token, root + '/commits/' + quote(branch, safe='')))
    sha = _sha(commit.get('sha'))
    tree = _sha(github._dict(github._dict(commit.get('commit')).get('tree')).get('sha'))
    rows = _tree(token, root, tree)
    for name in path.split('/') if path else []:
        item = next((r for r in rows if r.get('path') == name and r.get('type') == 'tree' and r.get('mode') == '040000'), None)
        if item is None:
            raise ValidationError('Dizin bulunamadı veya desteklenmiyor.')
        rows = _tree(token, root, item.get('sha'))
    return sha, rows


@github.bounded
def browse(account, project, path):
    path_value(path, directory=True)
    token, root, repo = authorized(account, project)
    sha, rows = directory(token, root, repo, path)
    entries = []
    for row in rows:
        name = row.get('path')
        if not isinstance(name, str) or '/' in name:
            continue
        child = (path + '/' if path else '') + name
        try:
            path_value(child)
        except ValidationError:
            continue
        folder = row.get('type') == 'tree' and row.get('mode') == '040000'
        regular = row.get('type') == 'blob' and row.get('mode') in ('100644', '100755')
        if not folder and not regular:
            continue
        entries.append({'name': name, 'path': child, 'type': 'directory' if folder else 'file',
                        'size': row.get('size') if regular else None})
    return {'path': path, 'source_commit': sha, 'entries': sorted(entries, key=lambda r: (r['type'] != 'directory', r['name'])), 'truncated': False}


def _blob(token, root, sha, expected_size):
    # Git's JSON blob endpoint encodes bytes in base64. Bound both wire and decoded bytes.
    deadline = github._budget.get()['deadline']
    remaining = min(2, deadline - time.monotonic())
    if remaining <= 0:
        github._error('github_response_limit')
    response = None
    try:
        response = requests.get('https://api.github.com' + root + '/git/blobs/' + _sha(sha), headers={
            'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28', 'Accept-Encoding': 'identity'},
            stream=True, allow_redirects=False, timeout=(remaining, remaining))
        if response.status_code != 200 or response.headers.get('Content-Encoding', 'identity') != 'identity':
            github._error()
        payload = bytearray()
        while True:
            if time.monotonic() > deadline:
                github._error('github_response_limit')
            # read1 returns available bytes rather than waiting for a full chunk.
            chunk = response.raw.read1(65536, decode_content=False)
            if not chunk:
                break
            payload.extend(chunk)
            if len(payload) > 16 * MIB or time.monotonic() > deadline:
                github._error('github_response_limit')
        data = json.loads(payload)
        if (not isinstance(data, dict) or data.get('encoding') != 'base64'
                or data.get('sha') != sha or data.get('size') != expected_size):
            github._error()
        if not isinstance(data.get('content'), str):
            github._error()
        raw = base64.b64decode(''.join(data['content'].split()), validate=True)
        if len(raw) != expected_size or hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() != sha:
            github._error()
        return raw
    except (requests.RequestException, HTTPError, OSError, ValueError, TypeError, KeyError):
        github._error()
    finally:
        if response is not None:
            response.close()


@github.bounded
def fetch(account, project, path):
    # Leave headroom for the 12-second raster worker within the 30-second
    # request timeout. Every JSON/tree/blob read shares this same budget.
    budget = github._budget.get()
    budget['deadline'] = min(budget['deadline'], time.monotonic() + 12)
    path_value(path)
    token, root, repo = authorized(account, project)
    parent, _, filename = path.rpartition('/')
    commit, rows = directory(token, root, repo, parent)
    row = next((r for r in rows if r.get('path') == filename), None)
    if not row or row.get('type') != 'blob' or row.get('mode') not in ('100644', '100755'):
        raise ValidationError('Yalnız normal dosyalar seçilebilir; symlink ve submodule desteklenmez.')
    size = row.get('size')
    if type(size) is not int or not 0 < size <= 10 * MIB:
        raise ValidationError('Dosya boş veya 10 MiB sınırını aşıyor.')
    raw = _blob(token, root, row.get('sha'), size)
    if raw.startswith(b'version https://git-lfs.github.com/spec/'):
        raise ValidationError('Git LFS dosyaları desteklenmiyor.')
    return filename, commit, raw
