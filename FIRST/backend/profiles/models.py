import uuid
from django.conf import settings
from django.db import models


class ProfileExtension(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='profile_extension')
    student_email = models.EmailField(max_length=254, blank=True, default='')
    student_verified_at = models.DateTimeField(null=True, blank=True)
    student_verified_until = models.DateTimeField(null=True, blank=True, db_index=True)
    student_request_nonce = models.CharField(max_length=64, blank=True, default='', editable=False)
    share_private_stats = models.BooleanField(default=False)
    contribution_stats = models.JSONField(default=dict, blank=True)
    stats_github_uid = models.CharField(max_length=255, blank=True, default='', editable=False)
    stats_updated_at = models.DateTimeField(null=True, blank=True)


class PortfolioRepository(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='portfolio_repositories')
    github_uid = models.CharField(max_length=255, editable=False)
    repository_id = models.PositiveBigIntegerField()
    repository_name = models.CharField(max_length=255)
    repository_url = models.URLField(max_length=500)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=1000, blank=True, default='')
    role = models.CharField(max_length=20, choices=[('owner', 'Sahip'), ('contributor', 'Katkıcı')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [models.UniqueConstraint(fields=['user', 'repository_id'], name='one_profile_repository')]


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='profile_certificates')
    title = models.CharField(max_length=200)
    filename = models.CharField(max_length=255)
    size = models.PositiveIntegerField()
    kind = models.CharField(max_length=16, choices=[('pdf', 'PDF'), ('image', 'JPEG')])
    content = models.JSONField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
