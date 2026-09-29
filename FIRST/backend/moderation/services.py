"""Shared deny gates: no GitHub, selected-viewer or team privilege is granted."""
from .models import ProfileVisibility, ProjectVisibility, UserRestriction


def enabled(user):
    return bool(user and getattr(user, 'is_authenticated', False) and user.is_active
        and not UserRestriction.objects.filter(user_id=user.pk, suspended=True).exists())


def administrator(user):
    return bool(user and getattr(user, 'is_superuser', False) and enabled(user) and user.email_verified)


def public_users(queryset):
    return queryset.filter(is_active=True).exclude(moderation_restriction__suspended=True).exclude(moderation_visibility__hidden=True)


def public_projects(queryset):
    return queryset.filter(owner__is_active=True).exclude(owner__moderation_restriction__suspended=True).exclude(moderation_visibility__hidden=True)


def profile_visible(user, actor=None):
    if not enabled(user):
        return False
    if not ProfileVisibility.objects.filter(user=user, hidden=True).exists():
        return True
    return bool(actor and getattr(actor, 'is_authenticated', False)
        and (actor.pk == user.pk or administrator(actor)))


def project_visible(project, actor=None):
    """Only a moderation gate. Callers must still apply ordinary project access."""
    if not enabled(project.owner):
        return False
    hidden = ProjectVisibility.objects.filter(project=project, hidden=True).exists()
    if not hidden:
        return True
    # The listing owner may manage hidden content; admin uses its own dashboard.
    return bool(actor and getattr(actor, 'is_authenticated', False) and actor.pk == project.owner_id)


def record_action(actor, action, target_type, target_id, reason='', previous=None, resulting=None):
    from .models import AuditEvent
    return AuditEvent.objects.create(actor=actor, actor_username=actor.username if actor else 'management',
        action=action, target_type=target_type, target_id=str(target_id), reason=reason,
        previous_state=previous or {}, resulting_state=resulting or {})
