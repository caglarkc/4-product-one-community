"""Local community teams; no GitHub access or remote side effects.

Lock order is identities (ascending PK), optional project, then team. No operation
acquires another identity after taking a team lock. Account deletion must call
assert_account_deletable while holding the deleting identity's row lock.
"""
from contextlib import contextmanager
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from accounts.account_views import locked_user
from accounts.models import User
from projects.models import Project
from .models import Team, Membership, TeamRequest, TeamBookmark


class Conflict(APIException):
    status_code = 409
    default_detail = 'Ekip durumu değişti. Sayfayı yenileyin.'


def eligible(user):
    if not user.is_active or not user.email_verified:
        raise PermissionDenied({'detail': 'Doğrulanmış e-posta gerekli.', 'code': 'email_verification_required'})


def role(team, user):
    if not user.is_authenticated:
        return None
    if team.owner_id == user.pk:
        return 'owner'
    return Membership.objects.filter(team=team, user=user).values_list('role', flat=True).first()


def require_manager(team, user):
    if role(team, user) not in ['owner', 'admin']:
        raise PermissionDenied('Bu işlem ekip yöneticisi gerektirir.')


def require_owner(team, user):
    if team.owner_id != user.pk:
        raise PermissionDenied('Bu işlem ekip sahibi gerektirir.')


@contextmanager
def locked(request, team_id, target_id=None, project_id=None):
    initial = get_object_or_404(Team, pk=team_id, is_active=True)
    initial_project = get_object_or_404(Project, pk=project_id) if project_id else None
    ids = {initial.owner_id, request.user.pk}
    if target_id is not None:
        ids.add(target_id)
    if initial_project:
        ids.add(initial_project.owner_id)
    with transaction.atomic():
        users = {u.pk: u for u in User.objects.select_for_update().filter(pk__in=ids).order_by('pk')}
        actor = locked_user(request)
        eligible(actor)
        project = get_object_or_404(Project.objects.select_for_update(), pk=project_id) if project_id else None
        team = get_object_or_404(Team.objects.select_for_update(), pk=team_id, is_active=True)
        if team.owner_id != initial.owner_id or (project and project.owner_id != initial_project.owner_id):
            raise Conflict()
        if not users.get(team.owner_id) or not users[team.owner_id].is_active:
            raise NotFound()
        if target_id is not None and (target_id not in users or not users[target_id].is_active):
            raise NotFound()
        yield actor, team, users, project


def assert_account_deletable(user):
    """Call within atomic(), after locking user, BEFORE provider cleanup/deletion."""
    teams = Team.objects.select_for_update().filter(owner=user, is_active=True).order_by('pk')
    for team in teams:
        if Membership.objects.filter(team=team).exclude(user=user).exists():
            raise ValidationError({'teams': ['Hesabınızı silmeden önce ekip sahipliğini devredin veya ekibi kapatın.']})


def team_data(team, user):
    return {'id': str(team.pk), 'name': team.name, 'description': team.description,
        'recruiting': team.recruiting, 'recruitment_text': team.recruitment_text,
        'skills': team.skills, 'organization_url': team.organization_url,
        'owner_username': team.owner.username, 'my_role': role(team, user), 'is_active': team.is_active,
        'saved': bool(user.is_authenticated and TeamBookmark.objects.filter(team=team, user=user).exists()),
        'created_at': team.created_at.isoformat(), 'updated_at': team.updated_at.isoformat()}


def request_data(row):
    return {'id': str(row.pk), 'team_id': str(row.team_id), 'team_name': row.team.name,
        'username': row.user.username, 'kind': row.kind, 'status': row.status,
        'explanation': row.explanation, 'created_at': row.created_at.isoformat()}


def open_request(team, user, kind, explanation=''):
    if Membership.objects.filter(team=team, user=user).exists():
        raise ValidationError('Bu kişi zaten ekip üyesi.')
    row = TeamRequest.objects.filter(team=team, user=user).first()
    if row and row.status == 'pending':
        # Never silently replace the other party's pending intent.
        raise Conflict('Bu ekip için bekleyen bir başvuru veya davet zaten var.')
    if row:
        row.kind, row.status, row.explanation = kind, 'pending', explanation
        row.save(update_fields=['kind', 'status', 'explanation', 'updated_at'])
    else:
        row = TeamRequest.objects.create(team=team, user=user, kind=kind, explanation=explanation)
    return row
