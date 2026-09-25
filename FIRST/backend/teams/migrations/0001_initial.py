import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('projects', '0005_community')]
    operations = [
        migrations.CreateModel(name='Team', fields=[
            ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ('name', models.CharField(max_length=100)),
            ('description', models.CharField(blank=True, default='', max_length=3000)),
            ('recruiting', models.BooleanField(default=False)),
            ('recruitment_text', models.CharField(blank=True, default='', max_length=2000)),
            ('skills', models.JSONField(blank=True, default=list)),
            ('organization_url', models.URLField(blank=True, default='', max_length=300)),
            ('is_active', models.BooleanField(default=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_teams', to=settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['-created_at', '-pk']}),
        migrations.CreateModel(name='Membership', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('role', models.CharField(choices=[('admin', 'Admin'), ('member', 'Member')], default='member', max_length=10)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='teams.team')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_memberships', to=settings.AUTH_USER_MODEL)),
        ], options={'constraints': [models.UniqueConstraint(fields=('team', 'user'), name='one_team_membership'),
            models.CheckConstraint(condition=models.Q(role__in=['admin', 'member']), name='valid_team_member_role')]}),
        migrations.CreateModel(name='TeamRequest', fields=[
            ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ('kind', models.CharField(choices=[('application', 'Application'), ('invitation', 'Invitation')], max_length=12)),
            ('status', models.CharField(default='pending', max_length=12)),
            ('explanation', models.CharField(blank=True, default='', max_length=2000)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to='teams.team')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['-created_at', '-pk'], 'constraints': [
            models.UniqueConstraint(fields=('team', 'user'), name='one_team_request_per_user'),
            models.CheckConstraint(condition=models.Q(kind__in=['application', 'invitation']), name='valid_team_request_kind'),
            models.CheckConstraint(condition=models.Q(status__in=['pending', 'accepted', 'rejected', 'withdrawn', 'declined']), name='valid_team_request_status')]}),
        migrations.CreateModel(name='TeamProject', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_links', to='teams.team')),
            ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='team_link', to='projects.project')),
        ]),
        migrations.CreateModel(name='TeamBookmark', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teams.team')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
        ], options={'ordering': ['-created_at', '-pk'], 'constraints': [
            models.UniqueConstraint(fields=('user', 'team'), name='one_team_bookmark')]}),
    ]
