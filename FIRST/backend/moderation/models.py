"""Moderation records preserve original account/project lifecycle flags."""
import uuid
from django.conf import settings
from django.db import models


class UserRestriction(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='moderation_restriction')
    suspended = models.BooleanField(default=False)
    reason = models.CharField(max_length=2000, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)


class ProfileVisibility(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='moderation_visibility')
    hidden = models.BooleanField(default=False)
    reason = models.CharField(max_length=2000, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)


class ProjectVisibility(models.Model):
    project = models.OneToOneField('projects.Project', on_delete=models.CASCADE, related_name='moderation_visibility')
    hidden = models.BooleanField(default=False)
    reason = models.CharField(max_length=2000, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)


class ReportReview(models.Model):
    report = models.OneToOneField('projects.Report', on_delete=models.CASCADE, related_name='administration_review')
    status = models.CharField(max_length=20, default='received', choices=[
        ('received', 'Alındı'), ('in_review', 'İnceleniyor'), ('resolved', 'Sonuçlandı'), ('dismissed', 'İşlem yapılmadı')])
    note = models.CharField(max_length=2000, blank=True, default='')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    actor_username = models.CharField(max_length=30)
    action = models.CharField(max_length=40)
    target_type = models.CharField(max_length=20)
    target_id = models.CharField(max_length=90)
    reason = models.CharField(max_length=2000, blank=True, default='')
    previous_state = models.JSONField(default=dict)
    resulting_state = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
