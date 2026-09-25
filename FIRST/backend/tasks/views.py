from django.core import signing
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from accounts import security
from accounts.account_views import ProtectedView, validated
from accounts.community_catalog import query_value
from accounts.proxy import client_ip
from accounts.serializers import StrictSerializer
from accounts.views import AuthView, RateLimited
from projects import participation, github_participation as gh
from projects.community import discoverable_projects
from projects.models import Project
from .models import Task
from . import provider


def throttle(request, write=False):
    identity = str(request.user.pk) if request.user.is_authenticated else client_ip(request)
    if security.count('tasks-write' if write else 'tasks-read', identity, ttl=60) > (10 if write else 30):
        raise RateLimited()


def data(row, own=False):
    ready = row.operation_state == 'ready'
    return {'id': str(row.pk), 'project_id': str(row.project_id), 'project_title': row.project.title,
        'issue_number': row.issue_number, 'title': row.title if ready else row.requested_title if own else '',
        'body': row.body if ready else row.requested_body if own else '', 'state': row.state,
        'issue_url': row.issue_url if ready else '', 'synced_at': row.synced_at.isoformat() if row.synced_at else None,
        'operation_state': row.operation_state, 'operation_error': row.operation_error if own else '',
        **({'request_id': str(row.request_id) if row.request_id else None} if own else {})}


def owner(actor, project):
    if actor.pk != project.owner_id or not project.is_active:
        raise NotFound()
    if project.is_private:
        raise ValidationError('Genel görevler yalnız public projelerde kullanılabilir.')
    return participation.eligible(actor)


def save_snapshot(row, snapshot):
    for key, value in snapshot.items():
        setattr(row, key, value)
    row.operation_state = 'ready'
    row.operation_error = ''
    row.synced_at = timezone.now()
    row.save()


class TaskInput(StrictSerializer):
    issue_number = serializers.IntegerField(min_value=1, required=False)
    title = serializers.CharField(max_length=200, required=False)
    body = serializers.CharField(max_length=10000, required=False, allow_blank=True)
    request_id = serializers.UUIDField(required=False)

    def validate(self, values):
        if 'issue_number' in values:
            if any(key in values for key in ['title', 'body', 'request_id']):
                raise ValidationError('Issue numarası veya yeni görev bilgileri kullanın.')
        elif not values.get('title') or not values.get('request_id'):
            raise ValidationError('Yeni Issue için başlık ve işlem kimliği gerekli.')
        return values


class FeedView(AuthView):
    def get(self, request):
        throttle(request)
        q = query_value(request, 'q').casefold()
        state = query_value(request, 'state', ['open', 'closed', 'all']) or 'open'
        project_id = query_value(request, 'project_id', limit=36)
        if project_id:
            project_id = str(serializers.UUIDField().run_validation(project_id))
        cursor = query_value(request, 'cursor', limit=1000)
        last = None
        if cursor:
            try:
                payload = signing.loads(cursor, salt='first-task-page', max_age=3600)
                if payload['filters'] != [q, state, project_id]:
                    raise ValueError()
                last = payload['last']
                serializers.UUIDField().run_validation(last)
            except (signing.BadSignature, KeyError, TypeError, ValueError):
                raise ValidationError('Sayfalama bağlantısı geçersiz. İlk sayfaya dönün.') from None
        rows = Task.objects.filter(project__in=discoverable_projects().filter(is_private=False), operation_state='ready').select_related('project__owner').order_by('-pk')
        if project_id:
            rows = rows.filter(project_id=project_id)
        if last:
            rows = rows.filter(pk__lt=last)
        candidates = list(rows[:13])
        has_more = len(candidates) > 12
        selected = candidates[:12]
        result, repositories = [], {}
        with gh.operation_budget():
            for row in selected:
                repo_id = row.project.repository_id
                if repo_id not in repositories:
                    repositories[repo_id] = provider.public_repository(row.project)
                if not repositories[repo_id]:
                    continue
                # Only public-verified snapshots participate in content filtering.
                if state != 'all' and row.state != state:
                    continue
                if q and q not in (row.title + ' ' + row.body + ' ' + row.project.title).casefold():
                    continue
                result.append(data(row))
        next_cursor = signing.dumps({'last': str(selected[-1].pk), 'filters': [q, state, project_id]}, salt='first-task-page') if has_more else None
        return Response({'tasks': result, 'next_cursor': next_cursor, 'has_more': has_more})


class ProjectTasksView(AuthView):
    def get(self, request, project_id):
        throttle(request)
        project = get_object_or_404(Project.objects.select_related('owner'), pk=project_id)
        participation.require_visible(project, request.user)
        if project.is_private:
            raise NotFound()
        own = request.user.is_authenticated and request.user.pk == project.owner_id
        with gh.operation_budget():
            if not provider.public_repository(project):
                raise NotFound()
        rows = Task.objects.filter(project=project).select_related('project').order_by('-created_at')
        if not own:
            rows = rows.filter(operation_state='ready')
        # Project task management bounded to the published-task cap.
        return Response({'tasks': [data(row, own) for row in rows[:50]]})

    def post(self, request, project_id):
        if not request.user.is_authenticated:
            raise PermissionDenied('Giriş yapın.')
        throttle(request, True)
        values = validated(TaskInput, request)
        with participation.locked(request, project_id) as (actor, project, users):
            account = owner(actor, project)
            if 'issue_number' in values:
                with gh.operation_budget():
                    gh._owner(account, project)
                    snapshot = provider.read_issue(project, values['issue_number'])
                row = Task.objects.filter(project=project, issue_number=values['issue_number']).first()
                if not row:
                    if Task.objects.filter(project=project).count() >= 50:
                        raise ValidationError('Bir projede en fazla 50 görev bağlantısı olabilir.')
                    row = Task(project=project, creator=actor)
                save_snapshot(row, snapshot)
                return Response({'task': data(row, True)}, status=201)
            row = Task.objects.filter(project=project, request_id=values['request_id']).first()
            if row:
                if (row.requested_title != values['title'] or row.requested_body != values.get('body', '')
                        or row.github_uid != account.uid):
                    raise participation.StateConflict('Aynı işlem kimliği farklı içerikle kullanılamaz.')
            else:
                if Task.objects.filter(project=project).count() >= 50:
                    raise ValidationError('Bir projede en fazla 50 görev bağlantısı olabilir.')
                row = Task.objects.create(project=project, creator=actor, github_uid=account.uid,
                    request_id=values['request_id'], requested_title=values['title'], requested_body=values.get('body', ''))
            task_id = row.pk
        return execute(request, task_id)


@gh.bounded
def execute(request, task_id):
    initial = get_object_or_404(Task, pk=task_id)
    with participation.locked(request, initial.project_id) as (actor, project, users):
        account = owner(actor, project)
        row = get_object_or_404(Task.objects.select_for_update(), pk=task_id)
        if row.operation_state == 'ready':
            return Response({'task': data(row, True)})
        if account.uid != row.github_uid or not row.request_id:
            raise PermissionDenied('İşlemi başlatan GitHub hesabı eşleşmiyor.')
        # Credentials, identity, current admin grant and public-repo status are
        # verified before a durable marker can make a later retry reconcile-only.
        authorization = provider.preflight(account, project)
        may_create = not row.operation_attempted
        row.operation_attempted = True
        row.operation_state = 'unknown'
        row.save(update_fields=['operation_attempted', 'operation_state'])
    # The attempted marker is durable even if this worker exits during GitHub POST.
    error = None
    with participation.locked(request, initial.project_id) as (actor, project, users):
        account = owner(actor, project)
        row = get_object_or_404(Task.objects.select_for_update(), pk=task_id)
        if account.uid != row.github_uid:
            raise PermissionDenied('GitHub kimliği değişti.')
        if row.operation_state == 'ready':
            return Response({'task': data(row, True)})
        try:
            with gh.operation_budget():
                snapshot = provider.create_or_reconcile(project, row, may_create, authorization)
            existing = Task.objects.filter(project=project, issue_number=snapshot['issue_number']).exclude(pk=row.pk).first()
            if existing:
                raise participation.StateConflict('Bu Issue zaten bağlı; mevcut görev bağlantısını kullanın.')
            save_snapshot(row, snapshot)
        except APIException as exc:
            row.operation_error = 'github_result_unknown'
            row.save(update_fields=['operation_error'])
            error = exc
    if error:
        raise error
    return Response({'task': data(row, True)})


class RefreshView(ProtectedView):
    def post(self, request, task_id):
        throttle(request, True)
        validated(StrictSerializer, request)
        initial = get_object_or_404(Task, pk=task_id)
        with participation.locked(request, initial.project_id) as (actor, project, users):
            account = owner(actor, project)
            row = get_object_or_404(Task.objects.select_for_update(), pk=task_id)
            if not row.issue_number or row.operation_state != 'ready':
                raise ValidationError('Önce oluşturma sonucunu doğrulayın.')
            with gh.operation_budget():
                gh._owner(account, project)
                save_snapshot(row, provider.read_issue(project, row.issue_number))
        return Response({'task': data(row, True)})


class RetryView(ProtectedView):
    def post(self, request, task_id):
        throttle(request, True)
        validated(StrictSerializer, request)
        return execute(request, task_id)


class DetailView(ProtectedView):
    def delete(self, request, task_id):
        throttle(request, True)
        validated(StrictSerializer, request)
        initial = get_object_or_404(Task, pk=task_id)
        with participation.locked(request, initial.project_id) as (actor, project, users):
            owner(actor, project)
            Task.objects.filter(pk=task_id).delete()
        return Response({'removed': True})
