from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from accounts.models import User
from moderation.services import enabled, record_action


class Command(BaseCommand):
    help = 'Grant FIRST administration to one explicitly identified, existing verified user.'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, required=True)
        parser.add_argument('--exclusive', action='store_true', help='Explicitly remove administrator privileges from other accounts.')

    def handle(self, *args, **options):
        user_id = options['user_id']
        with transaction.atomic():
            users = list(User.objects.select_for_update().filter(Q(pk=user_id) | Q(is_superuser=True)).order_by('pk'))
            owner = next((user for user in users if user.pk == user_id), None)
            if not owner or not owner.email_verified or not enabled(owner):
                raise CommandError('The target must be an existing active, email-verified account without suspension.')
            if options['exclusive']:
                for user in users:
                    if user.pk != user_id and user.is_superuser:
                        user.is_superuser = False
                        user.is_staff = False
                        user.save(update_fields=['is_superuser', 'is_staff'])
                        record_action(None, 'administrator_revoked', 'user', user.pk,
                            'Explicit exclusive administrator assignment.', {'administrator': True}, {'administrator': False})
            if not owner.is_superuser or not owner.is_staff:
                owner.is_superuser = True
                owner.is_staff = True
                owner.save(update_fields=['is_superuser', 'is_staff'])
                record_action(None, 'administrator_granted', 'user', owner.pk,
                    'Explicit administrator assignment by stable user ID.', {'administrator': False}, {'administrator': True})
        self.stdout.write(self.style.SUCCESS('FIRST administrator assigned to user ID ' + str(user_id) + '.'))
