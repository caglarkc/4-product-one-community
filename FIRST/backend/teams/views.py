"""Bounded, permission-checked FIRST team endpoints."""
from urllib.parse import urlsplit
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from accounts.account_views import ProtectedView, locked_user, validated
from accounts import security
from accounts.proxy import client_ip
from accounts.community_catalog import CatalogList, page_data, query_value, search
from accounts.models import User, username_key
from accounts.serializers import StrictSerializer
from accounts.views import AuthView, RateLimited
from projects.community_views import throttle
from projects.models import Project, ProjectViewer, Participation
from projects.views import public_project_summary
from .models import Team, Membership, TeamRequest, TeamProject, TeamBookmark
from . import services as s


class TeamInput(StrictSerializer):
    name = serializers.CharField(min_length=2, max_length=100)
    description = serializers.CharField(max_length=3000, allow_blank=True, required=False)
    recruiting = serializers.BooleanField(required=False)
    recruitment_text = serializers.CharField(max_length=2000, allow_blank=True, required=False)
    skills = CatalogList(required=False)
    organization_url = serializers.URLField(max_length=300, allow_blank=True, required=False)

    def validate_recruiting(self, value):
        if type(self.initial_data['recruiting']) is not bool:
            raise serializers.ValidationError('Boolean gereklidir.')
        return value

    def validate_organization_url(self, value):
        if not value:
            return ''
        parsed = urlsplit(value)
        parts = parsed.path.strip('/').split('/')
        if (parsed.scheme != 'https' or parsed.netloc != 'github.com' or len(parts) != 1
                or not parts[0] or not all(c.isascii() and (c.isalnum() or c == '-') for c in parts[0])
                or parsed.query or parsed.fragment):
            raise serializers.ValidationError('https://github.com/organizasyon biçimini kullanın.')
        return 'https://github.com/' + parts[0]


class UsernameInput(StrictSerializer):
    username = serializers.CharField(min_length=3, max_length=30)


class ApplicationInput(StrictSerializer):
    explanation = serializers.CharField(min_length=10, max_length=2000)


class ActionInput(StrictSerializer):
    action = serializers.ChoiceField(choices=['accept', 'reject', 'withdraw', 'decline'])


class RoleInput(StrictSerializer):
    role = serializers.ChoiceField(choices=['admin', 'member'])


class ProjectInput(StrictSerializer):
    project_id = serializers.UUIDField()


def target_user(username):
    if not 3 <= len(username) <= 30:
        raise NotFound()
    return get_object_or_404(User, username_normalized=username_key(username), is_active=True)


def available():
    return Team.objects.filter(is_active=True, owner__is_active=True).select_related('owner')


def collection_page(queryset, request, parameter, size=12):
    value = query_value(request, parameter, limit=9) or '1'
    if not value.isascii() or not value.isdecimal() or int(value) < 1:
        raise ValidationError({parameter: ['Sayfa pozitif bir tam sayı olmalıdır.']})
    page = int(value)
    count = queryset.count()
    start = (page - 1) * size
    return list(queryset[start:start + size]) if start < count else [], {
        'count': count, 'next_page': page + 1 if start + size < count else None,
        'previous_page': page - 1 if page > 1 else None}


def public_read_throttle(request):
    if security.count('team-public-read', client_ip(request), ttl=60) > 120:
        raise RateLimited()


class TeamsView(AuthView):
    def get(self, request):
        public_read_throttle(request)
        teams = search(available(), request, ['name', 'description', 'recruitment_text'])
        if query_value(request, 'recruiting', choices=['1']) == '1':
            teams = teams.filter(recruiting=True)
        rows, meta = page_data(teams, request)
        return Response({'teams': [s.team_data(t, request.user) for t in rows], **meta})

    def post(self, request):
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        throttle(request, 'team-create', 10)
        data = validated(TeamInput, request)
        with transaction.atomic():
            actor = locked_user(request)
            s.eligible(actor)
            team = Team.objects.create(owner=actor, **data)
            Membership.objects.create(team=team, user=actor, role='admin')
            result = s.team_data(team, actor)
        return Response({'team': result}, status=201)


class MineView(ProtectedView):
    def get(self, request):
        throttle(request, 'team-read', 60)
        teams = available().filter(memberships__user=request.user)
        invitations = TeamRequest.objects.filter(user=request.user, kind='invitation', status='pending',
            team__is_active=True, team__owner__is_active=True).select_related('team', 'user')
        teams, team_meta = collection_page(teams, request, 'page')
        invitations, invitation_meta = collection_page(invitations, request, 'invitations_page')
        return Response({'teams': [s.team_data(t, request.user) for t in teams],
                         'invitations': [s.request_data(r) for r in invitations],
                         'team_pagination': team_meta, 'invitation_pagination': invitation_meta})


class TeamDetailView(AuthView):
    def get(self, request, team_id):
        public_read_throttle(request)
        team = get_object_or_404(available(), pk=team_id)
        members = Membership.objects.filter(team=team, user__is_active=True).select_related('user').order_by('created_at', 'pk')
        manager = s.role(team, request.user) in ['owner', 'admin']
        requests = team.requests.filter(user__is_active=True, status='pending').select_related('user', 'team')
        if not manager:
            requests = requests.filter(user=request.user) if request.user.is_authenticated else requests.none()
        members, member_meta = collection_page(members, request, 'members_page')
        rows, request_meta = collection_page(requests, request, 'requests_page')
        mine = team.requests.filter(user=request.user).select_related('team', 'user').first() if request.user.is_authenticated else None
        # Team membership adds no permission; unlisted URLs must not be enumerated.
        # Do not expose a count of projects omitted by either privacy check.
        visibility = Q(visibility='public')
        if request.user.is_authenticated:
            viewers = ProjectViewer.objects.filter(user=request.user).values('project_id')
            invitations = Participation.objects.filter(user=request.user, kind='invitation').exclude(
                status__in=['declined', 'withdrawn', 'rejected']).values('project_id')
            visibility |= Q(owner=request.user) | (Q(visibility='selected') & (Q(pk__in=viewers) | Q(pk__in=invitations)))
        projects = Project.objects.filter(team_link__team=team, is_active=True, owner__is_active=True).filter(visibility).select_related('owner').order_by('-created_at', '-pk')
        projects, project_meta = collection_page(projects, request, 'projects_page')
        return Response({'team': s.team_data(team, request.user), 'members': [
            {'username': m.user.username, 'full_name': m.user.full_name,
             'role': 'owner' if m.user_id == team.owner_id else m.role} for m in members],
            'projects': [public_project_summary(project) for project in projects], 'requests': [s.request_data(r) for r in rows],
            'my_request': s.request_data(mine) if mine else None,
            'member_pagination': member_meta, 'request_pagination': request_meta, 'project_pagination': project_meta})

    def patch(self, request, team_id):
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        throttle(request)
        data = validated(TeamInput, request, partial=True)
        with s.locked(request, team_id) as (actor, team, users, project):
            s.require_manager(team, actor)
            for key, value in data.items():
                setattr(team, key, value)
            team.save()
            result = s.team_data(team, actor)
        return Response({'team': result})

    def delete(self, request, team_id):
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        throttle(request)
        validated(StrictSerializer, request)
        with s.locked(request, team_id) as (actor, team, users, project):
            s.require_owner(team, actor)
            team.is_active, team.recruiting = False, False
            team.save(update_fields=['is_active', 'recruiting', 'updated_at'])
            TeamProject.objects.filter(team=team).delete()
            team.requests.filter(status='pending', kind='application').update(status='rejected')
            team.requests.filter(status='pending', kind='invitation').update(status='withdrawn')
        return Response({'closed': True})


class ApplyView(ProtectedView):
    def post(self, request, team_id):
        throttle(request)
        data = validated(ApplicationInput, request)
        with s.locked(request, team_id) as (actor, team, users, project):
            if not team.recruiting:
                raise ValidationError('Ekip şu anda başvuru almıyor.')
            row = s.open_request(team, actor, 'application', data['explanation'])
            result = s.request_data(row)
        return Response({'request': result}, status=201)


class InvitationsView(ProtectedView):
    def post(self, request, team_id):
        throttle(request, 'team-invite', 20)
        target = target_user(validated(UsernameInput, request)['username'])
        with s.locked(request, team_id, target_id=target.pk) as (actor, team, users, project):
            s.require_manager(team, actor)
            target = users[target.pk]
            if not target.invitations_open:
                raise PermissionDenied('Bu kişi davet almıyor.')
            row = s.open_request(team, target, 'invitation')
            result = s.request_data(row)
        return Response({'request': result}, status=201)


class RequestActionView(ProtectedView):
    def post(self, request, team_id, request_id):
        throttle(request)
        action = validated(ActionInput, request)['action']
        initial = get_object_or_404(TeamRequest, pk=request_id, team_id=team_id)
        with s.locked(request, team_id, target_id=initial.user_id) as (actor, team, users, project):
            row = get_object_or_404(TeamRequest.objects.select_for_update().select_related('team', 'user'), pk=request_id, team=team)
            if row.status != 'pending':
                raise s.Conflict('Bu talep artık beklemiyor.')
            own = actor.pk == row.user_id
            if row.kind == 'application':
                if action == 'withdraw' and own:
                    row.status = 'withdrawn'
                elif action in ['accept', 'reject']:
                    s.require_manager(team, actor)
                    row.status = 'accepted' if action == 'accept' else 'rejected'
                else:
                    raise PermissionDenied('Bu başvuru için işlem yetkiniz yok.')
            elif own and action in ['accept', 'decline']:
                row.status = 'accepted' if action == 'accept' else 'declined'
            elif action == 'withdraw':
                s.require_manager(team, actor)
                row.status = 'withdrawn'
            else:
                raise PermissionDenied('Bu davet için işlem yetkiniz yok.')
            if row.status == 'accepted':
                s.eligible(users[row.user_id])
                Membership.objects.get_or_create(team=team, user=users[row.user_id], defaults={'role': 'member'})
            row.save(update_fields=['status', 'updated_at'])
            result = s.request_data(row)
        return Response({'request': result})


class MemberRoleView(ProtectedView):
    def post(self, request, team_id, username):
        throttle(request)
        new_role = validated(RoleInput, request)['role']
        target = target_user(username)
        with s.locked(request, team_id, target_id=target.pk) as (actor, team, users, project):
            s.require_owner(team, actor)
            if target.pk == team.owner_id:
                raise ValidationError('Sahip rolü yalnız sahiplik devriyle değişir.')
            member = get_object_or_404(Membership, team=team, user_id=target.pk)
            member.role = new_role
            member.save(update_fields=['role'])
        return Response({'role': new_role})


class MemberView(ProtectedView):
    def delete(self, request, team_id, username):
        throttle(request)
        validated(StrictSerializer, request)
        target = target_user(username)
        with s.locked(request, team_id, target_id=target.pk) as (actor, team, users, project):
            s.require_manager(team, actor)
            member = get_object_or_404(Membership, team=team, user_id=target.pk)
            if target.pk in [actor.pk, team.owner_id] or (member.role == 'admin' and team.owner_id != actor.pk):
                raise PermissionDenied('Bu üyeyi çıkaramazsınız; kendi üyeliğiniz için ayrıl işlemini kullanın.')
            member.delete()
        return Response({'removed': True})


class TransferView(ProtectedView):
    def post(self, request, team_id):
        throttle(request)
        target = target_user(validated(UsernameInput, request)['username'])
        with s.locked(request, team_id, target_id=target.pk) as (actor, team, users, project):
            s.require_owner(team, actor)
            if target.pk == actor.pk:
                raise ValidationError('Zaten ekip sahibisiniz.')
            s.eligible(users[target.pk])
            get_object_or_404(Membership, team=team, user_id=target.pk)
            Membership.objects.filter(team=team, user=actor).update(role='admin')
            team.owner = users[target.pk]
            team.save(update_fields=['owner', 'updated_at'])
            result = s.team_data(team, actor)
        return Response({'team': result})


class LeaveView(ProtectedView):
    def post(self, request, team_id):
        throttle(request)
        validated(StrictSerializer, request)
        with s.locked(request, team_id) as (actor, team, users, project):
            if actor.pk == team.owner_id:
                raise ValidationError('Önce sahipliği devredin veya ekibi kapatın.')
            get_object_or_404(Membership, team=team, user=actor).delete()
        return Response({'left': True})


class TeamProjectsView(ProtectedView):
    def post(self, request, team_id):
        throttle(request)
        project_id = validated(ProjectInput, request)['project_id']
        with s.locked(request, team_id, project_id=project_id) as (actor, team, users, project):
            s.require_manager(team, actor)
            if project.owner_id != actor.pk or not project.is_active:
                raise NotFound()
            existing = TeamProject.objects.filter(project=project).first()
            if existing and existing.team_id != team.pk:
                raise s.Conflict('Proje başka bir ekibe bağlı. Önce mevcut bağlantıyı kaldırın.')
            TeamProject.objects.get_or_create(team=team, project=project)
        return Response({'attached': True})


class TeamProjectView(ProtectedView):
    def delete(self, request, team_id, project_id):
        throttle(request)
        validated(StrictSerializer, request)
        with s.locked(request, team_id, project_id=project_id) as (actor, team, users, project):
            if actor.pk != project.owner_id:
                s.require_manager(team, actor)
            get_object_or_404(TeamProject, team=team, project=project).delete()
        return Response({'detached': True})


class BookmarkView(ProtectedView):
    def put(self, request, team_id):
        throttle(request)
        validated(StrictSerializer, request)
        with s.locked(request, team_id) as (actor, team, users, project):
            TeamBookmark.objects.get_or_create(user=actor, team=team)
        return Response({'saved': True})

    def delete(self, request, team_id):
        throttle(request)
        validated(StrictSerializer, request)
        with transaction.atomic():
            actor = locked_user(request)
            s.eligible(actor)
            TeamBookmark.objects.filter(user=actor, team_id=team_id).delete()
        return Response({'saved': False})


class BookmarksView(ProtectedView):
    def get(self, request):
        throttle(request, 'team-read', 60)
        rows, meta = page_data(available().filter(teambookmark__user=request.user), request)
        return Response({'teams': [s.team_data(t, request.user) for t in rows], **meta})
