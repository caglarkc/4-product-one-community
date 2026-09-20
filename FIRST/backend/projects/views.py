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
from . import github
from .models import GitHubCredential, Project
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


def project_data(project, repo=None, visible=True):
    # Stored privacy is never trusted to expose a URL: current provider proof only.
    private = repo['private'] if repo else True
    return {'id': str(project.pk), 'title': project.title, 'category': project.category,
        'subcategory': project.subcategory, 'stage': project.stage,
        'category_label': CATEGORY_LABELS.get(project.category, project.category or 'Belirtilmedi'),
        'subcategory_label': SUBCATEGORY_LABELS.get(project.category, {}).get(project.subcategory, project.subcategory or 'Belirtilmedi'),
        'stage_label': STAGE_LABELS.get(project.stage, project.stage or 'Belirtilmedi'),
        'description': project.description, 'readme_excerpt': project.readme_excerpt if visible else '',
        'is_private': private, 'repository_url': repo['html_url'] if repo and not private else None,
        'repository_name': repo['full_name'] if repo and not private else None,
        'is_active': project.is_active, 'created_at': project.created_at.isoformat(), 'updated_at': project.updated_at.isoformat()}


def public_project_summary(project):
    # Feed fields are intentionally independent of provider-backed detail data.
    return {'id': str(project.pk), 'title': project.title, 'description': project.description,
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
    title = serializers.CharField(max_length=200)
    category = serializers.ChoiceField(choices=list(CATEGORY_LABELS.items()))
    subcategory = serializers.ChoiceField(choices=SUBCATEGORY_CODES)
    stage = serializers.ChoiceField(choices=list(STAGE_LABELS.items()))
    description = serializers.CharField(max_length=5000, required=False, allow_blank=True, default='')
    readme_excerpt = serializers.CharField(max_length=600, required=False, allow_blank=True, default='')

    def validate(self, data):
        validate_classification(data['category'], data['subcategory'], data['stage'])
        return data


class EditInput(StrictSerializer):
    title = serializers.CharField(max_length=200, required=False)
    category = serializers.ChoiceField(choices=list(CATEGORY_LABELS.items()), required=False)
    subcategory = serializers.ChoiceField(choices=SUBCATEGORY_CODES, required=False)
    stage = serializers.ChoiceField(choices=list(STAGE_LABELS.items()), required=False)
    description = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)

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
        return Response({'categories': CATEGORIES, 'stages': STAGES, 'github_app_enabled': github.enabled()})


class StatusView(AuthView):
    def get(self, request):
        account = member(request)
        connected = False
        if account and github.enabled():
            try:
                token = github.access_token(account)
                identity = github.api(token, '/user')
                connected = type(identity.get('id')) is int and str(identity['id']) == account.uid
            except github.GitHubAccessError:
                pass
        return Response({'enabled': github.enabled(), 'connected': connected, 'github_linked': bool(account), 'credential_stored': bool(account and GitHubCredential.objects.filter(account=account).exists()), 'installation_url': installation_url()})


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
            github.save_tokens(account, tokens)
        return Response({'status': 'connected', 'return_to': flow.get('return_to', '/projelerim/yeni')})


class RepositoriesView(AuthView):
    def get(self, request):
        account = member(request, linked=True)
        _, repos = github.authorized_repositories(account)
        return Response({'repositories': repos})


class PreviewView(AuthView):
    def post(self, request):
        account = member(request, eligible=True)
        data = validate(SelectionInput, request.data)
        token, repo = github.repository(account, **data)
        return Response({'repository': repo, 'readme_excerpt': github.readme(token, repo)})


class MineView(AuthView):
    def get(self, request):
        member(request)
        # Own cards and editor fields need no live provider data. Keep repo
        # links hidden here; the detail endpoint proves current GitHub access.
        return Response({'projects': [project_data(project)
            for project in Project.objects.filter(owner=request.user)]})


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
        projects = Project.objects.filter(is_active=True, owner__is_active=True).order_by('-created_at', '-pk')
        count = projects.count()
        start = (page - 1) * page_size
        # Avoid sending an oversized OFFSET to the database for absent pages.
        rows = projects[start:start + page_size] if start < count else []
        return Response({'projects': [public_project_summary(project) for project in rows],
            'count': count, 'next_page': page + 1 if start + page_size < count else None,
            'previous_page': page - 1 if page > 1 else None})

    def post(self, request):
        account = member(request, eligible=True)
        data = validate(CreateInput, request.data)
        token, repo = github.repository(account, data['installation_id'], data['repository_id'])
        current_excerpt = github.readme(token, repo)
        if data['readme_excerpt'] and data['readme_excerpt'] != current_excerpt:
            raise ValidationError({'readme_excerpt': ['README değişti. Önizlemeyi yenileyin.']})
        try:
            with transaction.atomic():
                locked_user(request)
                if not SocialAccount.objects.filter(pk=account.pk, user=request.user).exists():
                    raise PermissionDenied('GitHub bağlantısı değişti.')
                project = Project.objects.create(owner=request.user, is_private=repo['private'], **data)
        except IntegrityError:
            raise Conflict() from None
        return Response({'project': project_data(project, repo)}, status=201)


class DetailView(AuthView):
    def get(self, request, project_id):
        if security.count('project-public-view', client_ip(request), ttl=60) > 30:
            raise RateLimited()
        project = get_object_or_404(Project, pk=project_id)
        own = request.user.is_authenticated and request.user.pk == project.owner_id
        if not project.is_active and not own:
            from rest_framework.exceptions import NotFound
            raise NotFound()
        account = SocialAccount.objects.filter(user_id=project.owner_id, provider='github').first()
        repo = None
        try:
            if account:
                _, repo = github.repository(account, project.installation_id, project.repository_id)
        except github.GitHubAccessError:
            pass
        return Response({'project': project_data(project, repo, visible=own or repo is not None)})

    def patch(self, request, project_id):
        account = member(request)
        project = get_object_or_404(Project, pk=project_id, owner=request.user)
        data = validate(EditInput, request.data)
        archive_only = data == {'is_active': False}
        repo = None
        if not archive_only:
            account = member(request, eligible=True)
            _, repo = github.repository(account, project.installation_id, project.repository_id)
        try:
            with transaction.atomic():
                locked_user(request)
                project = Project.objects.select_for_update().get(pk=project.pk, owner=request.user)
                if not archive_only:
                    validate_classification(
                        data.get('category', project.category),
                        data.get('subcategory', project.subcategory),
                        data.get('stage', project.stage),
                    )
                for field, value in data.items():
                    setattr(project, field, value)
                if repo:
                    project.is_private = repo['private']
                project.save()
        except IntegrityError:
            raise Conflict() from None
        return Response({'project': project_data(project, repo)})
