import uuid
from django.conf import settings
from django.db import models


class Snapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='showcase_files')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    github_uid = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    kind = models.CharField(max_length=16)
    size = models.PositiveIntegerField()
    source_commit = models.CharField(max_length=64)
    original = models.BinaryField(editable=False)
    content = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    published = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['created_at']
