"""Public Issue snapshots. An uncertain POST is reconciled, never repeated."""
import re
from projects import github_participation as gh


def public_repository(project):
    repo = gh._api(None, '/repositories/' + str(project.repository_id), missing=True)
    if repo is None:
        return None
    if not isinstance(repo, dict):
        gh._error('task_repository_mismatch')
    if repo.get('private') is not False:
        return None
    if (type(repo.get('id')) is not int or repo['id'] != project.repository_id
            or not isinstance(repo.get('full_name'), str)
            or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo['full_name'])):
        gh._error('task_repository_mismatch')
    return repo


def issue_data(row, repo, number):
    if (type(number) is not int or number <= 0 or not isinstance(row, dict)
            or 'pull_request' in row or type(row.get('number')) is not int or row.get('number') != number
            or row.get('state') not in ['open', 'closed'] or not isinstance(row.get('title'), str)
            or row.get('body') is not None and not isinstance(row.get('body'), str)):
        gh._error('task_issue_invalid')
    body = re.sub(r'<!-- FIRST task operation: [0-9a-f-]+ -->', '', row.get('body') or '').strip()
    return {'issue_number': number, 'title': row['title'][:200], 'body': body[:10000],
            'state': row['state'], 'issue_url': 'https://github.com/' + repo['full_name'] + '/issues/' + str(number)}


def read_issue(project, number):
    repo = public_repository(project)
    if not repo:
        gh._error('task_public_repository_required', 'Görev yalnız güncel public repodan gösterilebilir.')
    row = gh._api(None, '/repos/' + repo['full_name'] + '/issues/' + str(number))
    return issue_data(row, repo, number)


def preflight(account, project):
    """Read-only authorization must succeed before reserving a POST attempt."""
    token, path, repo = gh._owner(account, project)
    if repo['private']:
        gh._error('task_public_repository_required', 'Private repoda genel görev oluşturulamaz.')
    return token, path, repo


def create_or_reconcile(project, task, may_create, authorization):
    # Ephemeral authorization belongs to this invocation and never enters the DB.
    # A second _owner call here could fail before POST after intent was reserved.
    token, path, repo = authorization
    marker = '<!-- FIRST task operation: ' + str(task.pk) + ' -->'
    if not may_create:
        # A mutable marker cannot offer provider-level exactly-once delivery.
        # Reconciliation never issues another POST, even after a complete empty scan.
        # Inspect each bounded page before fetching the next: a recent match
        # must not depend on the total number of historical issues and PRs.
        for page in range(1, 11):
            rows = gh._api(token, path + '/issues', params={
                'state': 'all', 'sort': 'created', 'direction': 'desc',
                'page': page, 'per_page': 100})
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                gh._error()
            for row in rows:
                if 'pull_request' not in row and marker in str(row.get('body') or ''):
                    if str(gh._dict(row.get('user')).get('id')) != str(task.github_uid):
                        gh._error('task_creator_changed')
                    return read_issue(project, gh._number(row.get('number')))
            if len(rows) < 100:
                break
        else:
            gh._error('github_collection_limit', 'GitHub liste sınırı aşıldı; işlem güvenle doğrulanamadı.')
        gh._error('task_result_unknown', 'Issue sonucu doğrulanamadı. GitHub’da kontrol edip mevcut Issue numarasını bağlayın; otomatik ikinci Issue oluşturulmaz.')
    row = gh._api(token, path + '/issues', method='POST', data={
        'title': task.requested_title, 'body': task.requested_body + '\n\n' + marker})
    return read_issue(project, gh._number(gh._dict(row).get('number')))
