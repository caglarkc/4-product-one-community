import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('projects', '0005_community'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='UserRestriction', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('suspended', models.BooleanField(default=False)),
            ('reason', models.CharField(max_length=2000, blank=True, default='')),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, related_name='moderation_restriction')),
        ]),
        migrations.CreateModel(name='ProfileVisibility', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('hidden', models.BooleanField(default=False)),
            ('reason', models.CharField(max_length=2000, blank=True, default='')),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, related_name='moderation_visibility')),
        ]),
        migrations.CreateModel(name='ProjectVisibility', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('hidden', models.BooleanField(default=False)),
            ('reason', models.CharField(max_length=2000, blank=True, default='')),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='projects.project', related_name='moderation_visibility')),
        ]),
        migrations.CreateModel(name='ReportReview', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('status', models.CharField(max_length=20, default='received', choices=[('received', 'Alındı'), ('in_review', 'İnceleniyor'), ('resolved', 'Sonuçlandı'), ('dismissed', 'İşlem yapılmadı')])),
            ('note', models.CharField(max_length=2000, blank=True, default='')),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('report', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='projects.report', related_name='administration_review')),
            ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to=settings.AUTH_USER_MODEL, related_name='+')),
        ]),
        migrations.CreateModel(name='AuditEvent', fields=[
            ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
            ('actor_username', models.CharField(max_length=30)),
            ('action', models.CharField(max_length=40)),
            ('target_type', models.CharField(max_length=20)),
            ('target_id', models.CharField(max_length=90)),
            ('reason', models.CharField(max_length=2000, blank=True, default='')),
            ('previous_state', models.JSONField(default=dict)),
            ('resulting_state', models.JSONField(default=dict)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('actor', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to=settings.AUTH_USER_MODEL, related_name='+')),
        ], options={'ordering': ['-created_at', '-id']}),
    ]
