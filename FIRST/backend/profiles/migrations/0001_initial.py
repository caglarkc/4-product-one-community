import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name='ProfileExtension',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_email', models.EmailField(blank=True, default='', max_length=254)),
                ('student_verified_at', models.DateTimeField(blank=True, null=True)),
                ('student_verified_until', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('student_request_nonce', models.CharField(blank=True, default='', editable=False, max_length=64)),
                ('share_private_stats', models.BooleanField(default=False)),
                ('contribution_stats', models.JSONField(blank=True, default=dict)),
                ('stats_github_uid', models.CharField(blank=True, default='', editable=False, max_length=255)),
                ('stats_updated_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='profile_extension', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PortfolioRepository',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('github_uid', models.CharField(editable=False, max_length=255)),
                ('repository_id', models.PositiveBigIntegerField()),
                ('repository_name', models.CharField(max_length=255)),
                ('repository_url', models.URLField(max_length=500)),
                ('title', models.CharField(max_length=200)),
                ('description', models.CharField(blank=True, default='', max_length=1000)),
                ('role', models.CharField(choices=[('owner', 'Sahip'), ('contributor', 'Katkıcı')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                          related_name='portfolio_repositories', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at', '-pk'],
                     'constraints': [models.UniqueConstraint(fields=('user', 'repository_id'), name='one_profile_repository')]},
        ),
        migrations.CreateModel(
            name='Certificate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('filename', models.CharField(max_length=255)),
                ('size', models.PositiveIntegerField()),
                ('kind', models.CharField(choices=[('pdf', 'PDF'), ('image', 'JPEG')], max_length=16)),
                ('content', models.JSONField(editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                          related_name='profile_certificates', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at', '-pk']},
        ),
    ]
