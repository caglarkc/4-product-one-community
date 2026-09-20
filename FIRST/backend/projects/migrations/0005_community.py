import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('projects', '0004_participation'), ('accounts', '0004_community_profile')]
    operations = [
        migrations.AddField(model_name='project', name='technologies', field=models.JSONField(default=list, blank=True)),
        migrations.AddField(model_name='project', name='required_skills', field=models.JSONField(default=list, blank=True)),
        migrations.CreateModel(name='Bookmark', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.project')),
        ], options={'ordering': ['-created_at', '-pk'], 'constraints': [models.UniqueConstraint(fields=['user', 'project'], name='one_bookmark_per_user_project')]}),
        migrations.CreateModel(name='Report', fields=[
            ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ('reason', models.CharField(max_length=20)), ('description', models.CharField(max_length=2000)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, related_name='submitted_reports')),
            ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, related_name='profile_reports', null=True, blank=True)),
            ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.project', null=True, blank=True)),
        ], options={'constraints': [
            models.CheckConstraint(condition=(models.Q(project__isnull=False, profile__isnull=True) | models.Q(project__isnull=True, profile__isnull=False)), name='report_exactly_one_target'),
            models.UniqueConstraint(fields=['reporter', 'project'], name='one_report_per_project_reporter'),
            models.UniqueConstraint(fields=['reporter', 'profile'], name='one_report_per_profile_reporter'),
        ]}),
    ]
