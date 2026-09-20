import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('projects', '0003_repository_snapshots'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='project', name='need_type', field=models.CharField(max_length=20, blank=True, default='')),
        migrations.AddField(model_name='project', name='participation_mode', field=models.CharField(max_length=20, blank=True, default='')),
        migrations.AddField(model_name='project', name='visibility', field=models.CharField(max_length=20, default='public')),
        migrations.AddField(model_name='project', name='applications_open', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='project', name='current_state', field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='project', name='desired_outcome', field=models.TextField(blank=True, default='')),
        migrations.AddField(model_name='project', name='issue_number', field=models.PositiveIntegerField(null=True, blank=True)),
        migrations.AddField(model_name='project', name='issue_status', field=models.CharField(max_length=20, default='none')),
        migrations.AddField(model_name='project', name='issue_create_requested', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='project', name='issue_creator_uid', field=models.CharField(max_length=255, blank=True, default='')),
        migrations.CreateModel(name='ProjectViewer', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('project', models.ForeignKey(to='projects.project', related_name='viewers', on_delete=django.db.models.deletion.CASCADE)),
            ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
        ], options={'constraints': [models.UniqueConstraint(fields=['project', 'user'], name='one_project_viewer')]}),
        migrations.CreateModel(name='Participation', fields=[
            ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ('project', models.ForeignKey(to='projects.project', related_name='participations', on_delete=django.db.models.deletion.CASCADE)),
            ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE)),
            ('github_uid', models.CharField(max_length=255)),
            ('kind', models.CharField(max_length=20, default='application')),
            ('explanation', models.TextField(blank=True, default='')),
            ('status', models.CharField(max_length=24, default='pending')),
            ('pr_number', models.PositiveIntegerField(null=True, blank=True)),
            ('pr_sha', models.CharField(max_length=64, blank=True, default='')),
            ('decision', models.CharField(max_length=24, blank=True, default='')),
            ('github_status', models.CharField(max_length=24, blank=True, default='')),
            ('github_invitation_id', models.PositiveBigIntegerField(null=True, blank=True)),
            ('github_invitation_url', models.URLField(max_length=500, blank=True, default='')),
            ('operation_state', models.CharField(max_length=24, default='idle')),
            ('operation_error', models.CharField(max_length=100, blank=True, default='')),
            ('merged', models.BooleanField(default=False)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
        ], options={'ordering': ['-created_at'], 'constraints': [models.UniqueConstraint(fields=['project', 'user'], name='one_participation_per_project_user')]}),
        migrations.CreateModel(name='Notification', fields=[
            ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ('project', models.ForeignKey(to='projects.project', on_delete=django.db.models.deletion.CASCADE)),
            ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE)),
            ('kind', models.CharField(max_length=40)),
            ('message', models.CharField(max_length=300)),
            ('is_read', models.BooleanField(default=False)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
        ], options={'ordering': ['-created_at']}),
    ]
