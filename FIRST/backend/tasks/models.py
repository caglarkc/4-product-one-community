import uuid
from django.conf import settings
from django.db import models


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='issue_tasks')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    request_id = models.UUIDField(null=True, blank=True)
    github_uid = models.CharField(max_length=255, blank=True)
    requested_title = models.CharField(max_length=200, blank=True)
    requested_body = models.TextField(blank=True)
    issue_number = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    state = models.CharField(max_length=10, default='open')
    issue_url = models.URLField(max_length=500, blank=True)
    operation_state = models.CharField(max_length=20, default='pending')
    operation_attempted = models.BooleanField(default=False)
    operation_error = models.CharField(max_length=100, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [
            models.UniqueConstraint(fields=['project', 'issue_number'], name='one_task_per_project_issue'),
            models.UniqueConstraint(fields=['project', 'request_id'], name='one_task_per_create_request'),
        ]
