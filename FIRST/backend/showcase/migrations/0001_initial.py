import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('projects', '0005_community')]
    operations = [migrations.CreateModel(name='Snapshot', fields=[
        ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
        ('github_uid', models.CharField(max_length=255)),
        ('filename', models.CharField(max_length=255)),
        ('kind', models.CharField(max_length=16)),
        ('size', models.PositiveIntegerField()),
        ('source_commit', models.CharField(max_length=64)),
        ('original', models.BinaryField(editable=False)),
        ('content', models.JSONField()),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('expires_at', models.DateTimeField(null=True, blank=True, db_index=True)),
        ('published', models.BooleanField(default=False, db_index=True)),
        ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
        ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='showcase_files', to='projects.project')),
    ], options={'ordering': ['created_at']})]
