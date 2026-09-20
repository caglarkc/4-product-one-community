"""Bookmarks confer no access; reports record only and never moderate content."""
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from accounts import security
from accounts.account_views import ProtectedView, locked_user, validated
from accounts.community_catalog import REASONS, page_data
from accounts.models import User, username_key
from accounts.serializers import StrictSerializer
from accounts.views import RateLimited
from . import participation
from .models import Bookmark, Project, Report
from .views import public_project_summary


def throttle(request, scope='community-write', limit=30):
    if security.count(scope, str(request.user.pk), ttl=60) > limit:
        raise RateLimited()


class BookmarksView(ProtectedView):
    def get(self, request):
        throttle(request, 'bookmark-read', 60)
        rows, metadata = page_data(Bookmark.objects.filter(user=request.user).select_related('project__owner'), request)
        result = []
        for row in rows:
            available = row.project.is_active and participation.visible(row.project, request.user)
            result.append({'project_id': str(row.project_id), 'available': available,
                'project': public_project_summary(row.project) if available else None})
        return Response({'bookmarks': result, **metadata})


class BookmarkView(ProtectedView):
    def get(self, request, project_id):
        throttle(request, 'bookmark-read', 60)
        project = get_object_or_404(Project.objects.select_related('owner'), pk=project_id)
        participation.require_visible(project, request.user)
        return Response({'saved': Bookmark.objects.filter(user=request.user, project=project).exists()})

    def put(self, request, project_id):
        throttle(request)
        validated(StrictSerializer, request)
        with participation.locked(request, project_id) as (user, project, users):
            participation.require_visible(project, user)
            if not project.is_active:
                raise NotFound()
            Bookmark.objects.get_or_create(user=user, project=project)
        return Response({'saved': True})

    def delete(self, request, project_id):
        throttle(request)
        # Deliberately no target lookup: removal works after visibility is revoked.
        with transaction.atomic():
            user = locked_user(request)
            Bookmark.objects.filter(user=user, project_id=project_id).delete()
        return Response({'saved': False})


class ReportInput(StrictSerializer):
    target_type = serializers.ChoiceField(choices=['project', 'profile'])
    target_id = serializers.CharField(max_length=90)
    reason = serializers.ChoiceField(choices=[item['value'] for item in REASONS])
    description = serializers.CharField(min_length=10, max_length=2000)

    def validate(self, data):
        if data['target_type'] == 'project':
            data['target_id'] = serializers.UUIDField().run_validation(data['target_id'])
        else:
            data['target_id'] = username_key(data['target_id'])
        return data


class ReportsView(ProtectedView):
    def post(self, request):
        throttle(request, 'report-create', 10)
        data = validated(ReportInput, request)
        with transaction.atomic():
            # All writers lock identities in PK order before a project, as participation does.
            project = None
            if data['target_type'] == 'project':
                project = get_object_or_404(Project, pk=data['target_id'])
                target_pk = project.owner_id
            else:
                target_pk = get_object_or_404(User, username_normalized=data['target_id'], is_active=True).pk
            users = {user.pk: user for user in User.objects.select_for_update().filter(
                pk__in={request.user.pk, target_pk}).order_by('pk')}
            actor = locked_user(request)
            target = users.get(target_pk)
            if not target or not target.is_active:
                raise NotFound()
            if not actor.email_verified:
                raise PermissionDenied({'detail': 'Önce e-posta adresinizi doğrulayın.', 'code': 'email_verification_required'})
            if target.pk == actor.pk:
                raise ValidationError('Kendi içeriğinizi şikâyet edemezsiniz.')
            if project:
                project = get_object_or_404(Project.objects.select_for_update(), pk=project.pk)
                participation.require_visible(project, actor)
                lookup = {'project': project}
            else:
                if target.username_normalized != data['target_id']:
                    raise NotFound()
                lookup = {'profile': target}
            report, created = Report.objects.get_or_create(reporter=actor, **lookup,
                defaults={'reason': data['reason'], 'description': data['description']})
        return Response({'report': {'id': str(report.pk), 'status': 'received',
            'created_at': report.created_at.isoformat()}, 'created': created}, status=201 if created else 200)
