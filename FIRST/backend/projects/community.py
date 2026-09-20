from .models import Project


def discoverable_projects():
    return Project.objects.filter(is_active=True, owner__is_active=True, visibility='public',
        applications_open=True).exclude(need_type='bug', issue_status__in=['pending', 'failed', 'none']).select_related('owner').order_by('-created_at', '-pk')
