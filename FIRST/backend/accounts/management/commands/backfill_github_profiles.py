"""Fill legacy display metadata from public GitHub profiles, without auth changes."""
import re
import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from allauth.socialaccount.models import SocialAccount
from accounts.connected_accounts import provider_metadata, sanitize_metadata
from accounts.models import User


class Command(BaseCommand):
    help = 'Fill missing GitHub display fields by stable ID; never modifies identity or email.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limit', type=int, default=50)

    def handle(self, *args, **options):
        limit = options['limit']
        if not 1 <= limit <= 100:
            raise CommandError('limit must be between 1 and 100')
        counts = dict(scanned=0, updated=0, skipped=0, failed=0)
        fields = ('display_name', 'username', 'avatar_url', 'profile_url')
        for account in SocialAccount.objects.filter(provider='github').order_by('pk')[:limit]:
            counts['scanned'] += 1
            old = sanitize_metadata('github', account.extra_data)
            if all(old[field] for field in fields) or not re.fullmatch(r'[1-9][0-9]{0,19}', account.uid):
                counts['skipped'] += 1
                continue
            try:
                response = requests.get(f'https://api.github.com/user/{account.uid}',
                    headers={'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'},
                    timeout=10, allow_redirects=False)
                if response.status_code != 200:
                    counts['failed'] += 1
                    continue
                claims = response.json()
                if not isinstance(claims, dict) or type(claims.get('id')) is not int or str(claims['id']) != account.uid:
                    counts['failed'] += 1
                    continue
                fresh = provider_metadata('github', claims)  # ignores public email
            except (requests.RequestException, ValueError):
                counts['failed'] += 1
                continue
            with transaction.atomic():
                # Same lock order as auth. Re-read to preserve concurrent login updates.
                User.objects.select_for_update().filter(pk=account.user_id).first()
                current = SocialAccount.objects.select_for_update().filter(
                    pk=account.pk, user_id=account.user_id, provider='github', uid=account.uid).first()
                if not current:
                    counts['skipped'] += 1
                    continue
                merged = sanitize_metadata('github', current.extra_data)
                before = merged.copy()
                for field in fields:
                    if not merged[field]:
                        merged[field] = fresh[field]
                merged = sanitize_metadata('github', merged)
                if before == merged:
                    counts['skipped'] += 1
                    continue
                if not options['dry_run']:
                    current.extra_data = merged
                    current.save(update_fields=['extra_data'])
                counts['updated'] += 1
        self.stdout.write(' '.join(f'{key}={value}' for key, value in counts.items()) +
                          f" dry_run={str(options['dry_run']).lower()}")
