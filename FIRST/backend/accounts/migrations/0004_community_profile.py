from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0003_user_email_change_nonce')]
    operations = [
        migrations.AddField(model_name='user', name='bio', field=models.CharField(max_length=1000, blank=True, default='')),
        migrations.AddField(model_name='user', name='website', field=models.URLField(max_length=500, blank=True, default='')),
        migrations.AddField(model_name='user', name='skills', field=models.JSONField(default=list, blank=True)),
        migrations.AddField(model_name='user', name='interests', field=models.JSONField(default=list, blank=True)),
        migrations.AddField(model_name='user', name='discoverable', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='user', name='invitations_open', field=models.BooleanField(default=True)),
    ]
