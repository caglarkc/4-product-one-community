import uuid
from django.conf import settings
from django.db import models


class GitHubCredential(models.Model):
    account = models.OneToOneField('socialaccount.SocialAccount', on_delete=models.CASCADE)
    encrypted_tokens = models.TextField()
    expires_at = models.DateTimeField()
    refresh_expires_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)


class RepositoryCache(models.Model):
    credential = models.OneToOneField(GitHubCredential, on_delete=models.CASCADE)
    repositories = models.JSONField(default=list)
    cached_at = models.DateTimeField(null=True, blank=True)
    generation = models.UUIDField(default=uuid.uuid4, editable=False)


class PreparedRepository(models.Model):
    credential = models.ForeignKey(GitHubCredential, on_delete=models.CASCADE)
    installation_id = models.PositiveBigIntegerField()
    repository_id = models.PositiveBigIntegerField()
    preview_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cache_generation = models.UUIDField(editable=False)
    repository = models.JSONField()
    readme_excerpt = models.CharField(max_length=600, blank=True, default='')
    prepared_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['credential', 'installation_id', 'repository_id'],
                                                name='one_prepared_repository_per_credential')]


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    repository_id = models.PositiveBigIntegerField()
    installation_id = models.PositiveBigIntegerField()
    repository_name = models.CharField(max_length=255, blank=True, default='')
    repository_url = models.URLField(max_length=500, blank=True, default='')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=40)
    subcategory = models.CharField(max_length=40, blank=True, default='')
    stage = models.CharField(max_length=40, blank=True, default='')
    description = models.TextField(blank=True, default='')
    readme_excerpt = models.CharField(max_length=600, blank=True, default='')
    is_private = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    need_type = models.CharField(max_length=20, blank=True, default='')
    participation_mode = models.CharField(max_length=20, blank=True, default='')
    visibility = models.CharField(max_length=20, default='public')
    applications_open = models.BooleanField(default=False)
    current_state = models.TextField(blank=True, default='')
    desired_outcome = models.TextField(blank=True, default='')
    issue_number = models.PositiveIntegerField(null=True, blank=True)
    issue_status = models.CharField(max_length=20, default='none')
    issue_create_requested = models.BooleanField(default=False)
    issue_creator_uid = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['repository_id'], condition=models.Q(is_active=True), name='one_active_project_per_repository')]


class ProjectViewer(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='viewers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['project', 'user'], name='one_project_viewer')]


class Participation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='participations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    github_uid = models.CharField(max_length=255)
    kind = models.CharField(max_length=20, default='application')
    explanation = models.TextField(blank=True, default='')
    status = models.CharField(max_length=24, default='pending')
    pr_number = models.PositiveIntegerField(null=True, blank=True)
    pr_sha = models.CharField(max_length=64, blank=True, default='')
    decision = models.CharField(max_length=24, blank=True, default='')
    github_status = models.CharField(max_length=24, blank=True, default='')
    github_invitation_id = models.PositiveBigIntegerField(null=True, blank=True)
    github_invitation_url = models.URLField(max_length=500, blank=True, default='')
    operation_state = models.CharField(max_length=24, default='idle')
    operation_error = models.CharField(max_length=100, blank=True, default='')
    merged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['project', 'user'], name='one_participation_per_project_user')]


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    kind = models.CharField(max_length=40)
    message = models.CharField(max_length=300)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
