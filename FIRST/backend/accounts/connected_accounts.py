"""Presentation-only provider metadata; never used to establish account ownership."""
import re
from urllib.parse import urlsplit
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


def text(value, limit=150):
    return value.strip()[:limit] if isinstance(value, str) else ''


def safe_avatar(value, provider):
    value = text(value, 2048)
    try:
        url = urlsplit(value)
        host = url.hostname or ''
        allowed = host == 'avatars.githubusercontent.com' if provider == 'github' else (
            host == 'lh3.googleusercontent.com' or bool(re.fullmatch(r'lh[0-9]+\.googleusercontent\.com', host)))
        if (url.scheme == 'https' and allowed and not url.username and not url.password
                and url.port in (None, 443) and not url.fragment and not any(c.isspace() for c in value)):
            return value
    except ValueError:
        pass
    return ''


def sanitize_metadata(provider, data):
    data = data if isinstance(data, dict) else {}
    email = text(data.get('email'), 254).lower()
    try:
        validate_email(email)
    except ValidationError:
        email = ''
    username = text(data.get('username'), 39) if provider == 'github' else ''
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?', username):
        username = ''
    return {'display_name': text(data.get('display_name')), 'username': username, 'email': email,
            'avatar_url': safe_avatar(data.get('avatar_url'), provider),
            'profile_url': f'https://github.com/{username}' if username else ''}


def provider_metadata(provider, claims):
    return sanitize_metadata(provider, {'display_name': claims.get('name'),
        'username': claims.get('login') if provider == 'github' else '',
        'email': claims.get('verified_primary_email') if provider == 'github' else claims.get('email'),
        'avatar_url': claims.get('avatar_url') if provider == 'github' else claims.get('picture')})


def save_metadata(user, provider, profile):
    # Call only after successful ownership checks while the user row is locked.
    user.socialaccount_set.filter(provider=provider, uid=profile['sub']).update(
        extra_data=sanitize_metadata(provider, profile.get('display')))


def connected_accounts(user):
    return [{'provider': account.provider, **sanitize_metadata(account.provider, account.extra_data)}
            for account in user.socialaccount_set.filter(provider__in=['google', 'github']).order_by('provider', 'pk')]
