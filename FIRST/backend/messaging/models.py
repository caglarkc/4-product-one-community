import uuid
from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """Exactly two stable account identities; username changes preserve history."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lower_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lower_conversations')
    higher_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='higher_conversations')
    lower_read_id = models.PositiveBigIntegerField(default=0)
    higher_read_id = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['lower_user', 'higher_user'], name='one_direct_conversation_per_pair'),
            models.CheckConstraint(condition=models.Q(lower_user__lt=models.F('higher_user')), name='direct_conversation_ordered_pair'),
        ]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.CharField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']
        indexes = [models.Index(fields=['conversation', '-id'], name='direct_message_history')]
