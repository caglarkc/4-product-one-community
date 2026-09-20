from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from accounts.models import User, username_key
from accounts.serializers import StrictSerializer
from accounts.views import AuthView, RateLimited
from accounts import security
from .models import Project, ProjectViewer, Participation, Notification
from . import participation as logic
from . import github_participation as provider
from .views import member, validate, project_data


class ApplyInput(StrictSerializer):
    explanation = serializers.CharField(max_length=5000)
    pr_number = serializers.IntegerField(min_value=1, required=False)


class UsernameInput(StrictSerializer):
    username = serializers.CharField(max_length=30)


class ActionInput(StrictSerializer):
    action = serializers.ChoiceField(choices=['accept', 'accept_and_invite', 'reject', 'withdraw', 'decline', 'refresh'])
    expected_sha = serializers.RegexField(r'^[a-fA-F0-9]{40,64}$', required=False)


def throttle(request):
    if security.count('participation-actions', str(request.user.pk), ttl=60) > 15:
        raise RateLimited()


def response_action(row, error=None, status=200):
    data = {'participation': logic.participation_data(row)}
    if error and row.operation_error in ['github_pull_changed', 'github_pull_not_mergeable']:
        data.update({'detail': 'PR değişti veya birleştirilemiyor. Güncel PR durumunu inceleyip yeniden karar verin.',
                     'code': row.operation_error})
        return Response(data, status=409)
    if error:
        data['detail'] = 'GitHub işlemi tamamlanamadı. Aynı işlemi yeniden deneyin; kayıt korundu.'
        data['code'] = 'github_operation_failed'
        return Response(data, status=503)
    return Response(data, status=status)


def target_user(data):
    return get_object_or_404(User, username_normalized=username_key(data['username']), is_active=True)


class DashboardView(AuthView):
    def get(self, request):
        member(request)
        rows = Participation.objects.select_related('project', 'user')
        return Response({'sent': [logic.participation_data(row) for row in rows.filter(user=request.user)[:200]],
            'received': [logic.participation_data(row) for row in rows.filter(project__owner=request.user)[:200]]})


class ApplyView(AuthView):
    def post(self, request, project_id):
        member(request, eligible=True)
        throttle(request)
        data = validate(ApplyInput, request.data)
        automatic = False
        with logic.locked(request, project_id) as (actor, project, users):
            logic.require_visible(project, actor)
            account = logic.eligible(actor)
            existing = Participation.objects.filter(project=project, user=actor).first()
            if existing:
                return response_action(existing)
            if not logic.apply_available(project, actor):
                raise PermissionDenied('Bu ilan yeni başvuru almıyor.')
            mode = project.participation_mode
            pr_sha = ''
            if mode == 'pr':
                if project.is_private or not data.get('pr_number'):
                    raise ValidationError({'pr_number': ['Kendi açtığınız PR numarasını girin.']})
                pull = provider.check_pull_request(logic.account_for(users[project.owner_id]), project,
                    data['pr_number'], account)
                if pull['state'] != 'open' or pull['merged'] or pull.get('draft'):
                    raise ValidationError({'pr_number': ['Açık ve incelemeye hazır bir PR seçin.']})
                pr_sha = pull['sha']
            elif data.get('pr_number'):
                raise ValidationError({'pr_number': ['Bu katılım yönteminde PR numarası alınmıyor.']})
            automatic = mode == 'automatic'
            row = Participation.objects.create(project=project, user=actor, github_uid=account.uid,
                kind=mode if mode != 'application' else 'application', explanation=data['explanation'],
                pr_number=data.get('pr_number'), pr_sha=pr_sha,
                decision='accept' if automatic else '', operation_state='pending' if automatic else 'idle')
            logic.notify(project.owner_id, project, 'application_received', 'İlanınıza yeni bir katılım başvurusu geldi.')
        if automatic:
            row, error = logic.execute(request, row.pk)
            return response_action(row, error, status=201)
        return response_action(row, status=201)


class InvitationView(AuthView):
    def post(self, request, project_id):
        member(request, eligible=True)
        throttle(request)
        data = validate(UsernameInput, request.data)
        target = target_user(data)
        with logic.locked(request, project_id, target.pk) as (actor, project, users):
            if project.owner_id != actor.pk:
                raise NotFound()
            logic.eligible(actor)
            if not project.is_active:
                raise PermissionDenied('Arşivlenmiş ilana davet gönderilemez.')
            if project.need_type in ['feature', 'bug'] and project.issue_status != 'ready':
                raise PermissionDenied('Önce GitHub Issue bağlantısını tamamlayın.')
            if target.pk == actor.pk:
                raise ValidationError('Kendinizi davet edemezsiniz.')
            account = logic.eligible(users[target.pk])
            existing = Participation.objects.select_for_update().filter(project=project, user=target).first()
            if existing and existing.kind == 'invitation' and existing.status == 'invited':
                return response_action(existing)
            if existing:
                if existing.operation_state != 'idle' or existing.status not in ['pending', 'rejected', 'withdrawn', 'declined']:
                    raise logic.StateConflict('Mevcut katılım veya GitHub işlemi var; yeni davet gönderilemez.')
                # Explicit owner invitation replaces an uneffected FIRST decision.
                # Keep the prior explanation and PR reference as application context.
                row = existing
                row.kind = 'invitation'
                row.status = 'invited'
                row.github_uid = account.uid
                row.decision = ''
                row.operation_error = ''
                row.save()
            else:
                row = Participation.objects.create(project=project, user=target, github_uid=account.uid,
                                                   kind='invitation', status='invited')
            logic.notify(target.pk, project, 'participation_invitation', 'Bir projeye katılım daveti aldınız.')
        return response_action(row, status=201)


class ActionView(AuthView):
    def post(self, request, participation_id):
        member(request)
        throttle(request)
        data = validate(ActionInput, request.data)
        initial = get_object_or_404(Participation, pk=participation_id)
        remote = False
        with logic.locked(request, initial.project_id, initial.user_id) as (actor, project, users):
            row = Participation.objects.select_for_update().select_related('project', 'user').get(pk=initial.pk)
            own = actor.pk == project.owner_id
            applicant = actor.pk == row.user_id
            if not own and not applicant:
                raise NotFound()
            action = data['action']
            if action == 'refresh':
                if not row.github_status or row.operation_state != 'succeeded':
                    raise logic.StateConflict('Önce bekleyen GitHub işlemini yeniden deneyin.')
                target = logic.account_for(users[row.user_id], row.github_uid)
                result = provider.invitation_status(logic.account_for(users[project.owner_id]), project, target)
                row.github_status = result['status']
                row.github_invitation_id = result.get('invitation_id')
                row.github_invitation_url = result.get('url') or ''
                row.save()
                return response_action(row)
            if action in ['withdraw', 'decline', 'reject']:
                allowed = ((action == 'withdraw' and applicant and row.kind != 'invitation')
                    or (action == 'decline' and applicant and row.kind == 'invitation')
                    or (action == 'reject' and own and row.kind != 'invitation'))
                if not allowed:
                    raise PermissionDenied()
                new_status = {'withdraw': 'withdrawn', 'decline': 'declined', 'reject': 'rejected'}[action]
                if row.status == new_status:
                    return response_action(row)
                if row.status not in ['pending', 'invited'] or row.operation_state != 'idle':
                    raise logic.StateConflict()
                row.status = new_status
                row.save()
                logic.notify(row.user_id if own else project.owner_id, project, 'participation_updated', 'Katılım başvurusu durumu değişti.')
                return response_action(row)
            allowed = ((own and row.kind in ['application', 'pr'])
                or (applicant and row.kind in ['automatic', 'invitation']))
            if not allowed or (action == 'accept_and_invite' and row.kind != 'pr'):
                raise PermissionDenied()
            if row.operation_state == 'succeeded':
                if row.decision != action:
                    raise logic.StateConflict()
                return response_action(row)
            if row.status not in ['pending', 'invited']:
                raise logic.StateConflict()
            logic.eligible(actor)
            logic.account_for(users[row.user_id], row.github_uid)
            if row.decision and row.decision != action:
                raise logic.StateConflict('Başlatılan işlem aynı kararla tamamlanmalıdır.')
            if row.kind == 'pr':
                sha = data.get('expected_sha')
                if not sha:
                    raise ValidationError({'expected_sha': ['İncelediğiniz PR commit SHA değerini gönderin.']})
                if row.decision and row.pr_sha != sha:
                    raise logic.StateConflict('Devam eden işlemin commit değeri değiştirilemez.')
                row.pr_sha = sha
            row.decision = action
            row.operation_state = 'pending'
            row.operation_error = ''
            row.save()
            remote = True
        if remote:
            row, error = logic.execute(request, row.pk)
            return response_action(row, error)


class ViewersView(AuthView):
    def get(self, request, project_id):
        member(request)
        project = get_object_or_404(Project, pk=project_id, owner=request.user)
        return Response({'viewers': [{'username': v.user.username}
            for v in ProjectViewer.objects.filter(project=project).select_related('user')]})

    def post(self, request, project_id):
        return self.change(request, project_id, True)

    def delete(self, request, project_id):
        return self.change(request, project_id, False)

    def change(self, request, project_id, add):
        member(request)
        throttle(request)
        target = target_user(validate(UsernameInput, request.data))
        with logic.locked(request, project_id, target.pk) as (actor, project, users):
            if project.owner_id != actor.pk:
                raise NotFound()
            if add:
                ProjectViewer.objects.get_or_create(project=project, user=target)
            else:
                ProjectViewer.objects.filter(project=project, user=target).delete()
        return Response({'detail': 'Görüntüleme izni güncellendi.'})


class CollaborationView(AuthView):
    def post(self, request, project_id):
        member(request, linked=True)
        throttle(request)
        validate(StrictSerializer, request.data)
        with logic.locked(request, project_id) as (actor, project, users):
            logic.require_visible(project, actor)
            # Even an originally public listing may now reference a private repo.
            account = logic.account_for(actor)
            with provider.operation_budget():
                owner = logic.account_for(users[project.owner_id])
                pulls = provider.pull_requests(owner, project, reader_account=account)
                issue = provider.issue(owner, project, project.issue_number, reader_account=account) if project.issue_number and project.issue_status == 'ready' else None
                return Response({'pull_requests': pulls, 'issue': issue, 'repository_url': project.repository_url})



class IssueView(AuthView):
    def post(self, request, project_id):
        member(request, eligible=True)
        throttle(request)
        validate(StrictSerializer, request.data)
        project, error = logic.setup_issue(request, project_id)
        data = {'project': project_data(project, request.user)}
        if error:
            data.update({'detail': 'GitHub Issue işlemi tamamlanamadı. Yeniden deneyin.', 'code': 'github_issue_failed'})
        return Response(data, status=503 if error else 200)


class NotificationsView(AuthView):
    def get(self, request):
        member(request)
        return Response({'notifications': [{'id': str(n.pk), 'project_id': str(n.project_id),
            'kind': n.kind, 'message': n.message, 'is_read': n.is_read, 'created_at': n.created_at.isoformat()}
            for n in Notification.objects.filter(user=request.user)[:100]]})


class NotificationReadView(AuthView):
    def post(self, request, notification_id):
        member(request)
        validate(StrictSerializer, request.data)
        from django.db import transaction
        from accounts.account_views import locked_user
        with transaction.atomic():
            user = locked_user(request)
            notification = get_object_or_404(Notification, pk=notification_id, user=user)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        return Response({'detail': 'Bildirim okundu.'})
