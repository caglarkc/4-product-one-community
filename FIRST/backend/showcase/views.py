from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from accounts.views import AuthView, RateLimited
from accounts.serializers import StrictSerializer
from accounts import security
from projects.models import Project
from projects import participation as access
from projects import github_participation as github
from projects.views import member, validate
from .models import Snapshot
from . import provider
from .renderers import render

LIMITS = {'files': 3, 'text_bytes': 1048576, 'binary_bytes': 10485760, 'total_bytes': 20971520}


class PathInput(StrictSerializer):
    path = serializers.CharField(max_length=1024, trim_whitespace=False)


class PublishInput(StrictSerializer):
    preview_id = serializers.UUIDField()
    replace_id = serializers.UUIDField(required=False)
    confirmed = serializers.BooleanField()


def metadata(row):
    return {'id': str(row.pk), 'filename': row.filename, 'kind': row.kind, 'size': row.size,
            'source_commit': row.source_commit, 'created_at': row.created_at.isoformat()}


def throttle(request):
    if security.count('showcase-actions', str(request.user.pk), ttl=60) > 12:
        raise RateLimited()


def owner(actor, project):
    if actor.pk != project.owner_id:
        raise NotFound()
    return access.eligible(actor)


class SafeView(AuthView):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Vary'] = 'Cookie, Origin'
        return response


class FilesView(SafeView):
    def get(self, request, project_id):
        project = get_object_or_404(Project.objects.select_related('owner'), pk=project_id)
        access.require_visible(project, request.user)
        files = Snapshot.objects.filter(project=project, published=True).defer('original', 'content')
        return Response({'files': [metadata(row) for row in files], 'limits': LIMITS})


class PreviewView(SafeView):
    def get(self, request, project_id, file_id):
        project = get_object_or_404(Project.objects.select_related('owner'), pk=project_id)
        access.require_visible(project, request.user)
        row = get_object_or_404(Snapshot.objects.defer('original'), pk=file_id, project=project, published=True)
        return Response({'file': {**metadata(row), 'content': row.content}})


class BrowseView(SafeView):
    def get(self, request, project_id):
        member(request, eligible=True)
        throttle(request)
        with access.locked(request, project_id) as (actor, project, users):
            account = owner(actor, project)
            return Response(provider.browse(account, project, request.query_params.get('path', '')))


class PrepareView(SafeView):
    def post(self, request, project_id):
        member(request, eligible=True)
        throttle(request)
        data = validate(PathInput, request.data)
        # User -> project locking order matches account deletion and identity unlink.
        # Serialize conversion as well: one owner cannot run concurrent raster workers.
        with access.locked(request, project_id) as (actor, project, users):
            account = owner(actor, project)
            now = timezone.now()
            Snapshot.objects.filter(actor=actor, published=False, expires_at__lte=now).delete()
            pending = Snapshot.objects.filter(actor=actor, published=False)
            if pending.count() >= 3:
                raise ValidationError('En çok 3 bekleyen önizleme olabilir. Yayımlayın veya 30 dakikalık sürenin dolmasını bekleyin.')
            filename, commit, raw = provider.fetch(account, project, data['path'])
            if sum(pending.values_list('size', flat=True)) + len(raw) > LIMITS['total_bytes']:
                raise ValidationError('Bekleyen önizlemeler toplam 20 MiB sınırını aşıyor.')
            content = render(filename, raw)
            row = Snapshot.objects.create(project=project, actor=actor, github_uid=account.uid,
                filename=filename, kind=content['kind'], size=len(raw), source_commit=commit,
                original=raw, content=content, expires_at=timezone.now() + timedelta(minutes=30))
            return Response({'preview': {**metadata(row), 'expires_at': row.expires_at.isoformat(),
                                       'content': row.content}}, status=201)


class PublishView(SafeView):
    def post(self, request, project_id):
        member(request, eligible=True)
        throttle(request)
        data = validate(PublishInput, request.data)
        if not data['confirmed']:
            raise ValidationError('Bu içeriğin ilanı görebilen kişilerle paylaşılacağını onaylayın.')
        with access.locked(request, project_id) as (actor, project, users):
            account = owner(actor, project)
            with github.operation_budget():
                provider.authorized(account, project)
            row = get_object_or_404(Snapshot.objects.select_for_update().defer('original', 'content'),
                pk=data['preview_id'], project=project, actor=actor, github_uid=account.uid,
                published=False, expires_at__gt=timezone.now())
            replace = None
            if data.get('replace_id'):
                replace = get_object_or_404(Snapshot, pk=data['replace_id'], project=project, published=True)
            existing = Snapshot.objects.filter(project=project, published=True)
            if replace:
                existing = existing.exclude(pk=replace.pk)
            if existing.count() >= LIMITS['files'] or sum(existing.values_list('size', flat=True)) + row.size > LIMITS['total_bytes']:
                raise ValidationError('İlan başına 3 dosya ve toplam 20 MiB sınırı var. Bir dosyayı kaldırın veya değiştirin.')
            if replace:
                replace.delete()
            row.published = True
            row.expires_at = None
            row.save(update_fields=['published', 'expires_at'])
            return Response({'file': metadata(row)}, status=201)


class PreparedView(SafeView):
    def delete(self, request, project_id, preview_id):
        member(request)
        throttle(request)
        with access.locked(request, project_id) as (actor, project, users):
            if actor.pk != project.owner_id:
                raise NotFound()
            # Idempotent cancel; no GitHub access needed to erase private bytes.
            Snapshot.objects.filter(pk=preview_id, project=project, actor=actor, published=False).delete()
        return Response({'removed': True})


class FileView(SafeView):
    def delete(self, request, project_id, file_id):
        member(request)
        throttle(request)
        with access.locked(request, project_id) as (actor, project, users):
            # Removing published data remains possible even after GitHub unlink.
            if actor.pk != project.owner_id:
                raise NotFound()
            get_object_or_404(Snapshot, pk=file_id, project=project, published=True).delete()
        return Response({'removed': True})
