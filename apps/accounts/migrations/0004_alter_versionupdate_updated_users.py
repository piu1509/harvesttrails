# Generated by Django 5.0.6 on 2024-07-12 06:53

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_versionupdate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='versionupdate',
            name='updated_users',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]
