"""Owner administration: explicit privilege, reversible restrictions, audit trail."""
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from accounts import security
from accounts.account_views import ProtectedView, locked_user, revoke_all, validated
from accounts.community_catalog import page_data, query_value, search
from accounts.models import User
from accounts.serializers import StrictSerializer
from accounts.views import RateLimited
from projects.models import Project, Report
from .models import AuditEvent, ProfileVisibility, ProjectVisibility, ReportReview, UserRestriction
from .services import administrator, record_action

STATUSES = ['received', 'in_review', 'resolved', 'dismissed']


def throttle(request, scope='administration-read', limit=120):
    if security.count(scope, str(request.user.pk), ttl=60) > limit:
        raise RateLimited()


def require_administrator(user):
    if not administrator(user):
        raise PermissionDenied({'detail': 'Yönetici yetkisi gerekli.', 'code': 'administrator_required'})


class AdministratorView(ProtectedView):
    def check_permissions(self, request):
        super().check_permissions(request)
        require_administrator(request.user)


def user_data(user):
    restriction = getattr(user, 'moderation_restriction', None)
    visibility = getattr(user, 'moderation_visibility', None)
    return {'id': str(user.pk), 'username': user.username, 'full_name': user.full_name,
        'email': user.email, 'is_active': user.is_active, 'is_administrator': administrator(user),
        'profile_hidden': bool(visibility and visibility.hidden),
        'suspended': bool(restriction and restriction.suspended),
        'restriction_reason': restriction.reason if restriction else '',
        'profile_visibility_reason': visibility.reason if visibility else ''}


def project_data(project):
    visibility = getattr(project, 'moderation_visibility', None)
    return {'id': str(project.pk), 'title': project.title, 'owner_username': project.owner.username,
        'is_active': project.is_active, 'hidden': bool(visibility and visibility.hidden),
        'restriction_reason': visibility.reason if visibility else ''}


def report_data(report):
    review = getattr(report, 'administration_review', None)
    if report.project_id:
        project = report.project
        visibility = getattr(project, 'moderation_visibility', None)
        restriction = getattr(project.owner, 'moderation_restriction', None)
        target = {'type': 'project', 'id': str(project.pk), 'title': project.title,
            'username': project.owner.username, 'hidden': bool(visibility and visibility.hidden),
            'suspended': bool(restriction and restriction.suspended)}
    else:
        user = report.profile
        visibility = getattr(user, 'moderation_visibility', None)
        restriction = getattr(user, 'moderation_restriction', None)
        target = {'type': 'profile', 'id': str(user.pk), 'title': user.full_name,
            'username': user.username, 'hidden': bool(visibility and visibility.hidden),
            'suspended': bool(restriction and restriction.suspended)}
    return {'id': str(report.pk), 'reason': report.reason, 'description': report.description,
        'created_at': report.created_at.isoformat(),
        'reporter': {'username': report.reporter.username, 'full_name': report.reporter.full_name},
        'target': target, 'status': review.status if review else 'received',
        'note': review.note if review else '', 'reviewed_at': review.updated_at.isoformat() if review else None}


def reports_queryset():
    return Report.objects.select_related('reporter', 'profile__moderation_visibility',
        'profile__moderation_restriction', 'project__moderation_visibility',
        'project__owner__moderation_restriction', 'administration_review').order_by('-created_at', '-id')


class SummaryView(AdministratorView):
    def get(self, request):
        throttle(request)
        return Response({'summary': {
            'received_reports': Report.objects.exclude(administration_review__status__in=['in_review', 'resolved', 'dismissed']).count(),
            'in_review_reports': ReportReview.objects.filter(status='in_review').count(),
            'hidden_projects': ProjectVisibility.objects.filter(hidden=True).count(),
            'hidden_profiles': ProfileVisibility.objects.filter(hidden=True).count(),
            'suspended_users': UserRestriction.objects.filter(suspended=True).count(),
        }})


class ReportsView(AdministratorView):
    def get(self, request):
        throttle(request)
        status = query_value(request, 'status', choices=STATUSES, limit=20)
        query = reports_queryset()
        if status == 'received':
            query = query.filter(Q(administration_review__isnull=True) | Q(administration_review__status='received'))
        elif status:
            query = query.filter(administration_review__status=status)
        rows, metadata = page_data(query, request)
        return Response({'reports': [report_data(row) for row in rows], **metadata})


class ReviewInput(StrictSerializer):
    status = serializers.ChoiceField(choices=STATUSES)
    note = serializers.CharField(max_length=2000, allow_blank=True, default='')


class ReportView(AdministratorView):
    def patch(self, request, report_id):
        throttle(request, 'administration-write', 30)
        data = validated(ReviewInput, request)
        with transaction.atomic():
            actor = locked_user(request)
            require_administrator(actor)
            report = get_object_or_404(Report.objects.select_for_update(), pk=report_id)
            review, created = ReportReview.objects.get_or_create(report=report)
            previous = {'status': review.status, 'note': review.note}
            review.status, review.note, review.reviewer = data['status'], data['note'], actor
            review.save(update_fields=['status', 'note', 'reviewer', 'updated_at'])
            record_action(actor, 'report_reviewed', 'report', report.pk, data['note'], previous,
                {'status': review.status, 'note': review.note})
            result = report_data(reports_queryset().get(pk=report_id))
        return Response({'report': result})


class UsersView(AdministratorView):
    def get(self, request):
        throttle(request)
        query = User.objects.select_related('moderation_restriction', 'moderation_visibility').order_by('username_normalized', 'pk')
        query = search(query, request, ['username', 'full_name', 'email'])
        rows, metadata = page_data(query, request)
        return Response({'users': [user_data(row) for row in rows], **metadata})


class UserActionInput(StrictSerializer):
    action = serializers.ChoiceField(choices=['hide_profile', 'unhide_profile', 'suspend', 'reactivate'])
    reason = serializers.CharField(min_length=3, max_length=2000)


class UserView(AdministratorView):
    def patch(self, request, user_id):
        throttle(request, 'administration-write', 30)
        data = validated(UserActionInput, request)
        with transaction.atomic():
            users = {user.pk: user for user in User.objects.select_for_update().filter(
                pk__in={request.user.pk, user_id}).order_by('pk')}
            actor = locked_user(request)
            require_administrator(actor)
            target = users.get(user_id)
            if not target:
                raise ValidationError({'user': ['Hesap bulunamadı.']})
            action = data['action']
            if action == 'suspend' and target.is_superuser:
                raise ValidationError({'action': ['Yönetici hesabı askıya alınamaz.']})
            previous = user_data(target)
            if action in ['suspend', 'reactivate']:
                restriction, created = UserRestriction.objects.get_or_create(user=target)
                was_suspended = restriction.suspended
                restriction.suspended = action == 'suspend'
                restriction.reason = data['reason']
                restriction.save(update_fields=['suspended', 'reason', 'updated_at'])
                if restriction.suspended and not was_suspended:
                    # Reactivation never revives old sessions or resets lifecycle flags.
                    revoke_all(target)
            else:
                visibility, created = ProfileVisibility.objects.get_or_create(user=target)
                visibility.hidden = action == 'hide_profile'
                visibility.reason = data['reason']
                visibility.save(update_fields=['hidden', 'reason', 'updated_at'])
            # Clear related-object caches populated by the before-state snapshot.
            target._state.fields_cache.pop('moderation_restriction', None)
            target._state.fields_cache.pop('moderation_visibility', None)
            result = user_data(target)
            # Audit states avoid duplicating private account fields such as email.
            keys = ['profile_hidden', 'suspended', 'is_active']
            record_action(actor, action, 'user', target.pk, data['reason'],
                {key: previous[key] for key in keys}, {key: result[key] for key in keys})
        return Response({'user': result})


class ProjectsView(AdministratorView):
    def get(self, request):
        throttle(request)
        query = Project.objects.select_related('owner', 'moderation_visibility').order_by('-created_at', '-pk')
        query = search(query, request, ['title', 'owner__username'])
        rows, metadata = page_data(query, request)
        return Response({'projects': [project_data(row) for row in rows], **metadata})


class ProjectActionInput(StrictSerializer):
    action = serializers.ChoiceField(choices=['hide', 'unhide'])
    reason = serializers.CharField(min_length=3, max_length=2000)


class ProjectView(AdministratorView):
    def patch(self, request, project_id):
        throttle(request, 'administration-write', 30)
        data = validated(ProjectActionInput, request)
        initial = get_object_or_404(Project, pk=project_id)
        with transaction.atomic():
            users = {user.pk: user for user in User.objects.select_for_update().filter(
                pk__in={request.user.pk, initial.owner_id}).order_by('pk')}
            actor = locked_user(request)
            require_administrator(actor)
            project = get_object_or_404(Project.objects.select_for_update(), pk=project_id)
            if project.owner_id not in users:
                raise ValidationError('Proje sahibi değişti. Yeniden deneyin.')
            previous = project_data(project)
            visibility, created = ProjectVisibility.objects.get_or_create(project=project)
            visibility.hidden = data['action'] == 'hide'
            visibility.reason = data['reason']
            visibility.save(update_fields=['hidden', 'reason', 'updated_at'])
            project._state.fields_cache.pop('moderation_visibility', None)
            result = project_data(project)
            record_action(actor, 'project_' + data['action'], 'project', project.pk, data['reason'],
                {'hidden': previous['hidden'], 'is_active': previous['is_active']},
                {'hidden': result['hidden'], 'is_active': result['is_active']})
        return Response({'project': result})


class AuditView(AdministratorView):
    def get(self, request):
        throttle(request)
        rows, metadata = page_data(AuditEvent.objects.all(), request)
        return Response({'events': [{'id': str(row.pk), 'actor_username': row.actor_username,
            'action': row.action, 'target_type': row.target_type, 'target_id': row.target_id,
            'reason': row.reason, 'created_at': row.created_at.isoformat()} for row in rows], **metadata})
