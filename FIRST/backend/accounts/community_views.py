"""Public community data uses an explicit allow-list, never account serializers."""
from urllib.parse import urlsplit
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from . import security
from .account_views import ProtectedView, locked_user, validated
from .community_catalog import SKILLS, SKILL_IDS, REASONS, CatalogList, page_data, query_value, search
from .connected_accounts import connected_accounts
from .models import User, username_key
from .proxy import client_ip
from .serializers import StrictSerializer
from .views import AuthView, RateLimited
from projects.taxonomy import CATEGORIES

INTEREST_IDS = [item['value'] for item in CATEGORIES]


def public_profile(user):
    accounts = connected_accounts(user)
    github = next((item for item in accounts if item['provider'] == 'github'), {})
    avatar = github.get('avatar_url') or next((item['avatar_url'] for item in accounts if item['avatar_url']), '')
    return {'username': user.username, 'full_name': user.full_name, 'bio': user.bio,
        'website': user.website, 'skills': user.skills, 'interests': user.interests,
        'invitations_open': user.invitations_open, 'github_username': github.get('username', ''),
        'github_url': github.get('profile_url', ''), 'avatar_url': avatar}


def public_throttle(request):
    if security.count('community-read', client_ip(request), ttl=60) > 60:
        raise RateLimited()


class CommunityProfileInput(StrictSerializer):
    bio = serializers.CharField(max_length=1000, allow_blank=True, required=False)
    website = serializers.URLField(max_length=500, allow_blank=True, required=False)
    skills = CatalogList(required=False)
    interests = CatalogList(choices=INTEREST_IDS, limit=8, required=False)
    discoverable = serializers.BooleanField(required=False)
    invitations_open = serializers.BooleanField(required=False)

    def validate_website(self, value):
        if not value:
            return value
        url = urlsplit(value)
        if url.scheme not in ['http', 'https'] or url.username or url.password:
            raise ValidationError('HTTP veya HTTPS web bağlantısı girin.')
        return value

    def validate(self, attrs):
        for key in ['discoverable', 'invitations_open']:
            if key in self.initial_data and type(self.initial_data[key]) is not bool:
                raise ValidationError({key: ['Boolean gereklidir.']})
        return attrs


class CommunityConfigView(AuthView):
    def get(self, request):
        return Response({'skills': SKILLS, 'technologies': SKILLS,
            'interests': [{'value': item['value'], 'label': item['label']} for item in CATEGORIES],
            'report_reasons': REASONS})


class CommunityProfileView(ProtectedView):
    def get(self, request):
        return Response({'profile': {**public_profile(request.user), 'discoverable': request.user.discoverable}})

    def patch(self, request):
        if security.count('community-edit', str(request.user.pk), ttl=60) > 20:
            raise RateLimited()
        data = validated(CommunityProfileInput, request)
        with transaction.atomic():
            user = locked_user(request)
            for key, value in data.items():
                setattr(user, key, value)
            if data:
                user.save(update_fields=list(data))
        return Response({'profile': {**public_profile(user), 'discoverable': user.discoverable}})


class PeopleView(AuthView):
    def get(self, request):
        public_throttle(request)
        users = User.objects.filter(is_active=True, discoverable=True,
            socialaccount__provider='github').distinct().order_by('username_normalized', 'pk')
        users = search(users, request, ['username', 'full_name'])
        for parameter, field, choices in [('skill', 'skills', SKILL_IDS), ('interest', 'interests', INTEREST_IDS)]:
            value = query_value(request, parameter, choices)
            if value:
                users = users.filter(**{field + '__contains': [value]})
        rows, metadata = page_data(users, request)
        return Response({'people': [public_profile(user) for user in rows], **metadata})


class PersonView(AuthView):
    def get(self, request, username):
        public_throttle(request)
        user = get_object_or_404(User, username_normalized=username_key(username), is_active=True)
        from projects.views import public_project_summary
        from projects.community import discoverable_projects
        rows, metadata = page_data(discoverable_projects().filter(owner=user), request)
        return Response({'profile': public_profile(user),
            'projects': [public_project_summary(project) for project in rows], **metadata})
