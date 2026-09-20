import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('projects', '0002_project_classification')]

    operations = [
        migrations.AddField(
            model_name='project', name='repository_name',
            field=models.CharField(max_length=255, blank=True, default=''),
        ),
        migrations.AddField(
            model_name='project', name='repository_url',
            field=models.URLField(max_length=500, blank=True, default=''),
        ),
        migrations.CreateModel(
            name='RepositoryCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('repositories', models.JSONField(default=list)),
                ('cached_at', models.DateTimeField(null=True, blank=True)),
                ('generation', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('credential', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='projects.githubcredential')),
            ],
        ),
        migrations.CreateModel(
            name='PreparedRepository',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('installation_id', models.PositiveBigIntegerField()),
                ('repository_id', models.PositiveBigIntegerField()),
                ('preview_token', models.UUIDField(default=uuid.uuid4, unique=True, editable=False)),
                ('cache_generation', models.UUIDField(editable=False)),
                ('repository', models.JSONField()),
                ('readme_excerpt', models.CharField(max_length=600, blank=True, default='')),
                ('prepared_at', models.DateTimeField(auto_now=True)),
                ('credential', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.githubcredential')),
            ],
            options={'constraints': [models.UniqueConstraint(
                fields=('credential', 'installation_id', 'repository_id'),
                name='one_prepared_repository_per_credential')]},
        ),
    ]
