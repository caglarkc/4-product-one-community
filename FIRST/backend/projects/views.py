import base64
import hashlib
import secrets
from urllib.parse import urlencode
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, ValidationError, APIException
from rest_framework.response import Response
from accounts.oauth_response import OAuthDestinationMixin, validate_callback_query
from accounts import security
from accounts.serializers import StrictSerializer
from accounts.account_views import locked_user
from accounts.views import AuthView, RateLimited
from accounts.proxy import client_ip
from . import github, snapshots, participation
from . import github_participation as provider
from .models import GitHubCredential, PreparedRepository, Project, RepositoryCache
from .taxonomy import CATEGORIES, STAGES

CATEGORY_LABELS = {category['value']: category['label'] for category in CATEGORIES}
SUBCATEGORY_LABELS = {category['value']: {item['value']: item['label'] for item in category['subcategories']}
                      for category in CATEGORIES}
SUBCATEGORY_CODES = sorted({code for children in SUBCATEGORY_LABELS.values() for code in children})
STAGE_LABELS = {stage['value']: stage['label'] for stage in STAGES}


def validate_classification(category, subcategory, stage):
    errors = {}
    if category not in CATEGORY_LABELS:
        errors['category'] = ['Geçerli bir üst kategori seçin.']
    if subcategory not in SUBCATEGORY_LABELS.get(category, {}):
        errors['subcategory'] = ['Seçilen üst kategoriye ait bir alt kategori seçin.']
    if stage not in STAGE_LABELS:
        errors['stage'] = ['Geçerli bir proje durumu seçin.']
    if errors:
        raise ValidationError(errors)


def member(request, eligible=False, linked=False):
    if not request.user.is_authenticated:
        raise NotAuthenticated()
    account = SocialAccount.objects.filter(user=request.user, provider='github').first()
    if eligible:
        if not request.user.email_verified:
            raise PermissionDenied({'detail': 'Önce e-posta adresinizi doğrulayın.', 'code': 'email_verification_required'})
    if (eligible or linked) and not account:
        raise PermissionDenied({'detail': 'Önce GitHub hesabınızı bağlayın.', 'code': 'github_link_required'})
    return account


def installation_url():
    return 'https://github.com/apps/' + settings.GITHUB_APP_SLUG + '/installations/new' if github.enabled() else None


def project_data(project, user=None):
    # A publication is the owner's approved snapshot, independent of GitHub.
    private = project.is_private
    return {**participation.fields(project, user), 'id': str(project.pk), 'title': project.title, 'category': project.category,
        'subcategory': project.subcategory, 'stage': project.stage,
        'category_label': CATEGORY_LABELS.get(project.category, project.category or 'Belirtilmedi'),
        'subcategory_label': SUBCATEGORY_LABELS.get(project.category, {}).get(project.subcategory, project.subcategory or 'Belirtilmedi'),
        'stage_label': STAGE_LABELS.get(project.stage, project.stage or 'Belirtilmedi'),
        'description': project.description, 'readme_excerpt': project.readme_excerpt,
        'is_private': private, 'repository_url': (project.repository_url or None) if not private else None,
        'repository_name': (project.repository_name or None) if not private else None,
        'is_active': project.is_active, 'created_at': project.created_at.isoformat(), 'updated_at': project.updated_at.isoformat()}


def public_project_summary(project):
    # Feed fields are intentionally independent of provider-backed detail data.
    return {'id': str(project.pk), 'title': project.title, 'description': project.description,
        'need_type': project.need_type,
        'need_type_label': next((i['label'] for i in participation.NEEDS if i['value'] == project.need_type), 'Belirtilmedi'),
        'participation_mode': project.participation_mode,
        'participation_mode_label': next((i['label'] for i in participation.MODES if i['value'] == project.participation_mode), 'Belirtilmedi'),
        'category': project.category, 'subcategory': project.subcategory, 'stage': project.stage,
        'category_label': CATEGORY_LABELS.get(project.category, project.category or 'Belirtilmedi'),
        'subcategory_label': SUBCATEGORY_LABELS.get(project.category, {}).get(project.subcategory, project.subcategory or 'Belirtilmedi'),
        'stage_label': STAGE_LABELS.get(project.stage, project.stage or 'Belirtilmedi'),
        'created_at': project.created_at.isoformat(), 'updated_at': project.updated_at.isoformat()}


class StartInput(StrictSerializer):
    return_to = serializers.ChoiceField(choices=['/', '/hesap', '/projelerim/yeni'], required=False, default='/projelerim/yeni')


class SelectionInput(StrictSerializer):
    installation_id = serializers.IntegerField(min_value=1)
    repository_id = serializers.IntegerField(min_value=1)


class CreateInput(SelectionInput):
    preview_token = serializers.UUIDField()
    title = serializers.CharField(max_length=200)
    category = serializers.ChoiceField(choices=list(CATEGORY_LABELS.items()))
    subcategory = serializers.ChoiceField(choices=SUBCATEGORY_CODES)
    stage = serializers.ChoiceField(choices=list(STAGE_LABELS.items()))
    description = serializers.CharField(max_length=5000, required=False, allow_blank=True, default='')
    readme_excerpt = serializers.CharField(max_length=600, required=False, allow_blank=True, default='', trim_whitespace=False)

    need_type = serializers.ChoiceField(choices=[i['value'] for i in participation.NEEDS])
    participation_mode = serializers.ChoiceField(choices=[i['value'] for i in participation.MODES])
    visibility = serializers.ChoiceField(choices=[i['value'] for i in participation.VISIBILITIES])
    applications_open = serializers.BooleanField(required=False, default=True)
    current_state = serializers.CharField(max_length=5000, required=False, allow_blank=True, default='')
    desired_outcome = serializers.CharField(max_length=5000, required=False, allow_blank=True, default='')
    issue_number = serializers.IntegerField(min_value=1, required=False)
    create_issue = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        participation.validate_listing(data)
        validate_classification(data['category'], data['subcategory'], data['stage'])
        return data


class EditInput(StrictSerializer):
    title = serializers.CharField(max_length=200, required=False)
    category = serializers.ChoiceField(choices=list(CATEGORY_LABELS.items()), required=False)
    subcategory = serializers.ChoiceField(choices=SUBCATEGORY_CODES, required=False)
    stage = serializers.ChoiceField(choices=list(STAGE_LABELS.items()), required=False)
    description = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    visibility = serializers.ChoiceField(choices=[i['value'] for i in participation.VISIBILITIES], required=False)
    applications_open = serializers.BooleanField(required=False)
    current_state = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    desired_outcome = serializers.CharField(max_length=5000, required=False, allow_blank=True)

    def validate_is_active(self, value):
        if type(self.initial_data.get('is_active')) is not bool:
            raise serializers.ValidationError('Boolean gereklidir.')
        return value


def validate(cls, data):
    serializer = cls(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


class Conflict(APIException):
    status_code = 409
    default_detail = {'detail': 'Bu repo için aktif bir paylaşım zaten var.', 'code': 'repository_already_shared'}


class ConfigView(AuthView):
    def get(self, request):
        return Response({'categories': CATEGORIES, 'stages': STAGES, 'github_app_enabled': github.enabled(),
            'need_types': participation.NEEDS, 'participation_modes': participation.MODES,
            'visibilities': participation.VISIBILITIES})


class StatusView(AuthView):
    def get(self, request):
        account = member(request)
        stored = bool(account and GitHubCredential.objects.filter(account=account).exists())
        # Presence of a configured credential, never a live provider guarantee.
        return Response({'enabled': github.enabled(), 'connected': github.enabled() and stored,
            'github_linked': bool(account), 'credential_stored': stored, 'installation_url': installation_url()})


class StartView(AuthView):
    def post(self, request):
        member(request, linked=True)
        github.require_enabled()
        data = validate(StartInput, request.data)
        if security.count('github-app-start', str(request.user.pk)) > 20:
            raise RateLimited()
        binder = secrets.token_urlsafe(32)
        request.session['github_app_binder'] = binder
        verifier = secrets.token_urlsafe(48)
        with transaction.atomic():
            user = locked_user(request)
            account = SocialAccount.objects.filter(user=user, provider='github').first()
            if not account:
                raise PermissionDenied('GitHub bağlantısı değişti.')
            flow = {'binder': binder, 'verifier': verifier, 'user_id': user.pk,
                'uid': account.uid, 'account_id': account.pk, 'security_version': user.security_version,
                'session_hash': security.digest(request.session.session_key), 'return_to': data['return_to']}
            state = security.issue_token('github-app-state', flow, 600)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        return Response({'authorization_url': 'https://github.com/login/oauth/authorize?' + urlencode({
            'client_id': settings.GITHUB_APP_CLIENT_ID, 'redirect_uri': settings.GITHUB_APP_REDIRECT_URI,
            'state': state, 'code_challenge': challenge, 'code_challenge_method': 'S256'})})


class CallbackView(OAuthDestinationMixin, AuthView):
    oauth_provider = 'github_app'
    oauth_callback = True

    def get(self, request):
        validate_callback_query(request)
        account = member(request, linked=True)
        github.require_enabled()
        state = request.query_params.get('state', '')
        if not state or len(state) > 128 or len(request.query_params.getlist('state')) != 1:
            raise PermissionDenied('Geçersiz GitHub doğrulaması.')
        flow = security.peek_token('github-app-state', state)
        binder = request.session.get('github_app_binder', '')
        if (not flow or not binder or not secrets.compare_digest(binder, flow.get('binder', ''))
                or flow.get('user_id') != request.user.pk or flow.get('account_id') != account.pk or flow.get('uid') != account.uid
                or flow.get('security_version') != request.user.security_version
                or flow.get('session_hash') != security.digest(request.session.session_key)):
            raise PermissionDenied('Geçersiz GitHub doğrulaması.')
        if security.consume_token('github-app-state', state) != flow:
            raise PermissionDenied('GitHub doğrulaması daha önce kullanıldı.')
        request.session.pop('github_app_binder', None)
        code = request.query_params.get('code', '')
        if request.query_params.get('error') or not code or len(code) > 4096 or len(request.query_params.getlist('code')) != 1:
            raise PermissionDenied('GitHub doğrulaması tamamlanamadı.')
        tokens = github.token_request({'code': code, 'code_verifier': flow['verifier'], 'redirect_uri': settings.GITHUB_APP_REDIRECT_URI})
        identity = github.api(tokens['access_token'], '/user')
        if type(identity.get('id')) is not int or str(identity['id']) != account.uid:
            raise PermissionDenied({'detail': 'Hesabınıza bağlı GitHub hesabını seçin.', 'code': 'github_identity_mismatch'})
        with transaction.atomic():
            # Recheck session expiry/revocation after GitHub requests and share
            # the user-first lock order with logout and session revocation.
            user = locked_user(request)
            if user.security_version != flow['security_version'] or not SocialAccount.objects.filter(pk=account.pk, user=user, uid=flow['uid']).exists():
                raise PermissionDenied('GitHub bağlantısı değişti.')
            credential = github.save_tokens(account, tokens)
            RepositoryCache.objects.filter(credential=credential).delete()
            PreparedRepository.objects.filter(credential=credential).delete()
        return Response({'status': 'connected', 'return_to': flow.get('return_to', '/projelerim/yeni')})


class RepositoriesView(AuthView):
    def get(self, request):
        member(request, linked=True)
        return Response(snapshots.repositories(request))

    def post(self, request):
        member(request, linked=True)
        validate(StrictSerializer, request.data)
        return Response(snapshots.repositories(request, refresh=True))


class PreviewView(AuthView):
    def post(self, request):
        member(request, eligible=True)
        data = validate(SelectionInput, request.data)
        return Response(snapshots.prepare(request, data))


class IssueChoicesView(AuthView):
    def post(self, request):
        member(request, eligible=True)
        data = validate(SelectionInput, request.data)
        if security.count('github-issue-choices', str(request.user.pk), ttl=60) > 5:
            raise RateLimited()
        with transaction.atomic():
            user, account, credential = snapshots.connection(request, eligible=True)
            cache = RepositoryCache.objects.filter(credential=credential, cached_at__isnull=False).first()
            selected = next((row for row in cache.repositories
                if row.get('id') == data['repository_id'] and row.get('installation_id') == data['installation_id']), None) if cache else None
            if not selected:
                raise snapshots.SnapshotChanged()
            project = Project(owner=user, repository_id=data['repository_id'], installation_id=data['installation_id'])
            issues = provider.selectable_issues(account, project)
            return Response({'issues': issues, 'limit': 50})


class MineView(AuthView):
    def get(self, request):
        member(request)
        # Reading an existing publication never contacts its external source.
        return Response({'projects': [project_data(project, request.user)
            for project in Project.objects.filter(owner=request.user).select_related('owner')]})


class CreateView(AuthView):
    def get(self, request):
        if security.count('project-public-feed', client_ip(request), ttl=60) > 30:
            raise RateLimited()
        pages = request.query_params.getlist('page')
        page_value = pages[0] if pages else '1'
        if (len(pages) > 1 or not page_value.isascii() or not page_value.isdecimal()
                or len(page_value) > 1000):
            raise ValidationError({'page': ['Sayfa pozitif bir tam sayı olmalıdır.']})
        page = int(page_value)
        if page < 1:
            raise ValidationError({'page': ['Sayfa pozitif bir tam sayı olmalıdır.']})
        page_size = 12
        projects = Project.objects.filter(is_active=True, owner__is_active=True, visibility='public',
            applications_open=True).exclude(need_type='bug', issue_status__in=['pending', 'failed', 'none']).select_related('owner').order_by('-created_at', '-pk')
        for field, choices in [('category', CATEGORY_LABELS), ('subcategory', SUBCATEGORY_CODES),
                ('stage', STAGE_LABELS), ('need_type', [i['value'] for i in participation.NEEDS]),
                ('participation_mode', [i['value'] for i in participation.MODES])]:
            values = request.query_params.getlist(field)
            if len(values) > 1 or (values and values[0] not in choices):
                raise ValidationError({field: ['Geçerli bir filtre seçin.']})
            if values:
                projects = projects.filter(**{field: values[0]})
        count = projects.count()
        start = (page - 1) * page_size
        # Avoid sending an oversized OFFSET to the database for absent pages.
        rows = projects[start:start + page_size] if start < count else []
        return Response({'projects': [public_project_summary(project) for project in rows],
            'count': count, 'next_page': page + 1 if start + page_size < count else None,
            'previous_page': page - 1 if page > 1 else None})

    def post(self, request):
        member(request, eligible=True)
        if security.count('participation-actions', str(request.user.pk), ttl=60) > 15:
            raise RateLimited()
        data = validate(CreateInput, request.data)
        preview_token = data.pop('preview_token')
        try:
            with transaction.atomic():
                user, account, credential = snapshots.connection(request, eligible=True)
                preview = PreparedRepository.objects.select_for_update().filter(credential=credential,
                    installation_id=data['installation_id'], repository_id=data['repository_id'],
                    preview_token=preview_token).first()
                if not preview or not RepositoryCache.objects.filter(credential=credential,
                        generation=preview.cache_generation, cached_at__isnull=False).exists():
                    raise snapshots.SnapshotChanged()
                if data['readme_excerpt'] and data['readme_excerpt'] != preview.readme_excerpt:
                    raise ValidationError({'readme_excerpt': ['Onayladığınız README özeti eşleşmiyor. Paylaşımı yeniden hazırlayın.']})
                repo = preview.repository
                participation.validate_listing(data, private=repo['private'])
                create_issue = data.pop('create_issue')
                project = Project(owner=user, is_private=repo['private'],
                    repository_name=repo['full_name'], repository_url=repo['html_url'], **data)
                if data['need_type'] == 'bug':
                    with provider.operation_budget():
                        if data.get('issue_number'):
                            provider.bug_issue(account, project, data['issue_number'])
                        else:
                            provider.require_public_issue_repository(account, project)
                if data['participation_mode'] == 'automatic':
                    provider.automatic_access_safety(account, project)
                project = Project.objects.create(owner=user, is_private=repo['private'],
                    repository_name=repo['full_name'], repository_url=repo['html_url'],
                    issue_create_requested=create_issue, issue_creator_uid=account.uid if create_issue else '',
                    issue_status='pending' if data['need_type'] == 'bug' else 'none', **data)
                preview.delete()
        except IntegrityError:
            raise Conflict() from None
        setup_error = None
        if project.need_type == 'bug':
            project, setup_error = participation.setup_issue(request, project.pk)
        result = {'project': project_data(project, request.user)}
        if setup_error:
            result['setup_error'] = 'GitHub Issue hazırlanamadı. İlan detayından yeniden deneyin.'
        return Response(result, status=201)


class DetailView(AuthView):
    def get(self, request, project_id):
        if security.count('project-public-view', client_ip(request), ttl=60) > 30:
            raise RateLimited()
        project = get_object_or_404(Project.objects.select_related('owner'), pk=project_id)
        participation.require_visible(project, request.user)
        from .models import Participation
        row = Participation.objects.filter(project=project, user=request.user).select_related('project', 'user').first() if request.user.is_authenticated else None
        return Response({'project': project_data(project, request.user),
            'participation': participation.participation_data(row) if row else None})

    def patch(self, request, project_id):
        member(request)
        project = get_object_or_404(Project, pk=project_id, owner=request.user)
        data = validate(EditInput, request.data)
        archive_only = data == {'is_active': False}
        try:
            with transaction.atomic():
                user = locked_user(request)
                project = Project.objects.select_for_update().get(pk=project.pk, owner=request.user)
                if not archive_only:
                    if not user.email_verified:
                        raise PermissionDenied({'detail': 'Önce e-posta adresinizi doğrulayın.', 'code': 'email_verification_required'})
                    validate_classification(
                        data.get('category', project.category),
                        data.get('subcategory', project.subcategory),
                        data.get('stage', project.stage),
                    )
                if not archive_only:
                    participation.validate_listing(data, project=project, private=project.is_private)
                for field, value in data.items():
                    setattr(project, field, value)
                project.save()
        except IntegrityError:
            raise Conflict() from None
        return Response({'project': project_data(project, request.user)})
