"""Listing permissions and durable collaboration actions.

Provider operations are reserved in a committed row before execution. Retries
reconcile the same GitHub identity and decision; user locks serialize unlinking.
"""
from contextlib import contextmanager
from allauth.socialaccount.models import SocialAccount
from django.db import transaction
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from accounts.account_views import locked_user
from accounts.models import User
from . import github_participation as provider
from .models import Project, ProjectViewer, Participation, Notification

NEEDS = [{'value': value, 'label': label} for value, label in [
    ('teammate', 'Ekip arkadaşı'), ('contributor', 'Contributor'),
    ('feature', 'Özellik geliştirme'), ('bug', 'Hata / sorun çözme')]]
MODES = [{'value': value, 'label': label} for value, label in [
    ('application', 'Başvuruyla kabul'), ('automatic', 'Otomatik katılım'), ('pr', 'Önce PR ile katkı')]]
VISIBILITIES = [{'value': value, 'label': label} for value, label in [
    ('public', 'Keşifte herkese açık'), ('link', 'Yalnız bağlantıyla'), ('selected', 'Yalnız seçilen kişiler')]]


class StateConflict(APIException):
    status_code = 409
    default_detail = {'detail': 'İşlem durumu değişti. Sayfayı yenileyin.', 'code': 'participation_conflict'}


def account_for(user, expected_uid=None):
    account = SocialAccount.objects.filter(user=user, provider='github').first()
    if not account or (expected_uid is not None and account.uid != expected_uid):
        raise PermissionDenied({'detail': 'Başvurudaki GitHub kimliği ile bağlı hesabınız eşleşmiyor.',
                                'code': 'github_identity_changed'})
    return account


def eligible(user):
    if not user.is_active or not user.email_verified:
        raise PermissionDenied({'detail': 'Doğrulanmış e-posta gerekli.', 'code': 'email_verification_required'})
    return account_for(user)


@contextmanager
def locked(request, project_id, other_user_id=None):
    # All identity locks have a global order, including owner and applicant.
    initial = Project.objects.filter(pk=project_id).first()
    if not initial:
        raise NotFound()
    ids = {initial.owner_id, request.user.pk}
    if other_user_id is not None:
        ids.add(other_user_id)
    with transaction.atomic():
        users = {u.pk: u for u in User.objects.select_for_update().filter(pk__in=ids).order_by('pk')}
        actor = locked_user(request)
        project = Project.objects.select_for_update().get(pk=project_id)
        if project.owner_id not in users:
            raise StateConflict()
        yield actor, project, users


def visible(project, user):
    if not project.owner.is_active:
        return False
    own = user.is_authenticated and user.pk == project.owner_id
    if own:
        return True
    if not project.is_active:
        return False
    if project.visibility != 'selected':
        return True
    return bool(user.is_authenticated and (
        ProjectViewer.objects.filter(project=project, user=user).exists()
        or Participation.objects.filter(project=project, user=user, kind='invitation')
            .exclude(status__in=['declined', 'withdrawn', 'rejected']).exists()))


def require_visible(project, user):
    if not visible(project, user):
        raise NotFound()


def apply_available(project, user):
    return bool(project.is_active and project.applications_open and project.visibility != 'selected'
                and project.participation_mode and project.owner.is_active
                and (project.need_type not in ['feature', 'bug'] or project.issue_status == 'ready')
                and not (user.is_authenticated and user.pk == project.owner_id))


def fields(project, user=None):
    return {'need_type': project.need_type, 'participation_mode': project.participation_mode,
        'need_type_label': next((i['label'] for i in NEEDS if i['value'] == project.need_type), 'Belirtilmedi'),
        'participation_mode_label': next((i['label'] for i in MODES if i['value'] == project.participation_mode), 'Belirtilmedi'),
        'visibility': project.visibility, 'applications_open': project.applications_open,
        'current_state': project.current_state, 'desired_outcome': project.desired_outcome,
        'issue_number': project.issue_number if not project.is_private else None,
        'issue_status': project.issue_status, 'owner_username': project.owner.username,
        'is_owner': bool(user and user.is_authenticated and user.pk == project.owner_id),
        'can_apply': apply_available(project, user) if user is not None else False}


def participation_data(row):
    return {'id': str(row.pk), 'project_id': str(row.project_id), 'project_title': row.project.title,
        'username': row.user.username, 'kind': row.kind, 'explanation': row.explanation,
        'status': row.status, 'pr_number': row.pr_number if not row.project.is_private else None,
        'pr_sha': row.pr_sha if not row.project.is_private else '', 'decision': row.decision,
        'github_status': row.github_status, 'github_invitation_id': row.github_invitation_id,
        'github_invitation_url': row.github_invitation_url,
        'operation_state': row.operation_state, 'operation_error': row.operation_error,
        'merged': row.merged, 'created_at': row.created_at.isoformat(), 'updated_at': row.updated_at.isoformat()}


def notify(user_id, project, kind, message):
    Notification.objects.create(user_id=user_id, project=project, kind=kind, message=message)


def validate_listing(data, project=None, private=False):
    need = data.get('need_type', project.need_type if project else '')
    mode = data.get('participation_mode', project.participation_mode if project else '')
    visibility = data.get('visibility', project.visibility if project else 'public')
    opened = data.get('applications_open', project.applications_open if project else True)
    if private and mode == 'pr':
        raise ValidationError({'participation_mode': ['Private repo için PR şartlı katılım kullanılamaz.']})
    if not opened and visibility == 'public':
        data['visibility'] = 'link'
    if need in ['feature', 'bug']:
        for field in ['current_state', 'desired_outcome']:
            if not data.get(field, getattr(project, field, '') if project else '').strip():
                raise ValidationError({field: ['Bu alan özellik/hata ilanında zorunludur.']})
        if project is None and bool(data.get('issue_number')) == bool(data.get('create_issue')):
            raise ValidationError({'issue_number': ['Mevcut Issue seçin veya yeni Issue oluşturun.']})
    elif project is None and any(data.get(key) for key in ['issue_number', 'create_issue', 'current_state', 'desired_outcome']):
        raise ValidationError({'need_type': ['Issue alanları yalnız özellik/hata ilanları içindir.']})
    if opened and not mode:
        raise ValidationError({'participation_mode': ['İlan katılım yöntemi eksik. Yeni ilan oluşturun.']})


def setup_issue(request, project_id):
    error = None
    with locked(request, project_id) as (actor, project, users):
        if actor.pk != project.owner_id:
            raise NotFound()
        eligible(actor)
        if project.need_type not in ['feature', 'bug']:
            raise ValidationError('Bu ilanda Issue yok.')
        if project.issue_status == 'ready':
            return project, None
        project.issue_status = 'pending'
        project.save(update_fields=['issue_status', 'updated_at'])
    with locked(request, project_id) as (actor, project, users):
        try:
            account = eligible(actor)
            if project.issue_status == 'ready':
                return project, None
            if project.issue_create_requested:
                if account.uid != project.issue_creator_uid:
                    raise PermissionDenied({'detail': 'Issue oluşturma işlemini başlatan GitHub hesabı değişti.',
                                            'code': 'github_issue_operation_identity_changed'})
                issue = provider.create_issue(account, project, project.title,
                    f"Mevcut durum\n\n{project.current_state}\n\nBeklenen sonuç\n\n{project.desired_outcome}",
                    operation_key=str(project.pk))
            else:
                issue = provider.issue(account, project, project.issue_number, reader_account=account)
            project.issue_number = issue['number']
            project.issue_status = 'ready'
        except APIException as exc:
            project.issue_status = 'failed'
            error = exc
        project.save(update_fields=['issue_number', 'issue_status', 'updated_at'])
    return project, error


def execute(request, participation_id):
    initial = Participation.objects.select_related('project').get(pk=participation_id)
    error = None
    with locked(request, initial.project_id, initial.user_id) as (actor, project, users):
        row = Participation.objects.select_for_update().select_related('user', 'project').get(pk=participation_id)
        if row.operation_state == 'succeeded':
            return row, None
        if row.operation_state not in ['pending', 'failed'] or not row.decision:
            raise StateConflict()
        try:
            owner = users[project.owner_id]
            applicant = users[row.user_id]
            eligible(actor)
            owner_account = eligible(owner)
            applicant_account = eligible(applicant)
            if applicant_account.uid != row.github_uid:
                raise PermissionDenied('Başvurudaki GitHub hesabı değişti.')
            with provider.operation_budget():
                if row.kind == 'pr':
                    result = provider.merge_pull_request(owner_account, project, row.pr_number,
                        applicant_account, row.pr_sha)
                    row.merged = bool(result.get('merged'))
                    if not row.merged:
                        raise StateConflict('PR birleştirilmedi.')
                if row.kind != 'pr' or row.decision == 'accept_and_invite':
                    result = provider.invite_collaborator(owner_account, project, applicant_account,
                        automatic=row.kind == 'automatic')
                    row.github_status = result['status']
                    row.github_invitation_id = result.get('invitation_id')
                    row.github_invitation_url = result.get('url') or ''
            row.status = 'accepted'
            row.operation_state = 'succeeded'
            row.operation_error = ''
            notify(row.user_id, project, 'participation_accepted', 'Katılım kabul edildi. GitHub davet durumunu kontrol edin.')
            if actor.pk != project.owner_id:
                notify(project.owner_id, project, 'participation_accepted', 'Bir katılımcı daveti kabul etti.')
        except APIException as exc:
            row.operation_state = 'failed'
            row.operation_error = 'github_operation_failed'
            code = str(exc.detail.get('code', '')) if isinstance(exc.detail, dict) else ''
            if code in ['github_pull_changed', 'github_pull_not_mergeable'] and not row.merged:
                # Provider proves the merge was not attempted; a new reviewed SHA is safe.
                row.operation_state = 'idle'
                row.operation_error = code
                row.decision = ''
            error = exc
        row.save()
    return row, error
