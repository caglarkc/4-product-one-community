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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['repository_id'], condition=models.Q(is_active=True), name='one_active_project_per_repository')]
