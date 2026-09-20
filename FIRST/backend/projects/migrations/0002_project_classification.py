from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('projects', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='project',
            name='subcategory',
            field=models.CharField(max_length=40, blank=True, default=''),
        ),
        migrations.AddField(
            model_name='project',
            name='stage',
            field=models.CharField(max_length=40, blank=True, default=''),
        ),
    ]
