import uuid
from django.conf import settings
from django.db import models


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_teams')
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=3000, blank=True, default='')
    recruiting = models.BooleanField(default=False)
    recruitment_text = models.CharField(max_length=2000, blank=True, default='')
    skills = models.JSONField(default=list, blank=True)
    organization_url = models.URLField(max_length=300, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class Membership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_memberships')
    # Owner is represented once, by Team.owner; its membership role is ignored.
    role = models.CharField(max_length=10, choices=[('admin', 'Admin'), ('member', 'Member')], default='member')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['team', 'user'], name='one_team_membership'),
                       models.CheckConstraint(condition=models.Q(role__in=['admin', 'member']), name='valid_team_member_role')]


class TeamRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=12, choices=[('application', 'Application'), ('invitation', 'Invitation')])
    status = models.CharField(max_length=12, default='pending')
    explanation = models.CharField(max_length=2000, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [models.UniqueConstraint(fields=['team', 'user'], name='one_team_request_per_user'),
            models.CheckConstraint(condition=models.Q(kind__in=['application', 'invitation']), name='valid_team_request_kind'),
            models.CheckConstraint(condition=models.Q(status__in=['pending', 'accepted', 'rejected', 'withdrawn', 'declined']), name='valid_team_request_status')]


class TeamProject(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='project_links')
    project = models.OneToOneField('projects.Project', on_delete=models.CASCADE, related_name='team_link')
    created_at = models.DateTimeField(auto_now_add=True)


class TeamBookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [models.UniqueConstraint(fields=['user', 'team'], name='one_team_bookmark')]
