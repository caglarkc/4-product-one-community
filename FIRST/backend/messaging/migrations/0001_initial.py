import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Conversation', fields=[
            ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ('lower_read_id', models.PositiveBigIntegerField(default=0)),
            ('higher_read_id', models.PositiveBigIntegerField(default=0)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now_add=True)),
            ('lower_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, related_name='lower_conversations')),
            ('higher_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, related_name='higher_conversations')),
        ], options={'ordering': ['-updated_at', '-id'], 'constraints': [
            models.UniqueConstraint(fields=['lower_user', 'higher_user'], name='one_direct_conversation_per_pair'),
            models.CheckConstraint(condition=models.Q(lower_user__lt=models.F('higher_user')), name='direct_conversation_ordered_pair'),
        ]}),
        migrations.CreateModel(name='Message', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('body', models.CharField(max_length=5000)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='messaging.conversation', related_name='messages')),
            ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['-id'], 'indexes': [models.Index(fields=['conversation', '-id'], name='direct_message_history')]}),
    ]
