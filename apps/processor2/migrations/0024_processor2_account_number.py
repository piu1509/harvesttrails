# Generated by Django 5.0.6 on 2024-11-12 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processor2', '0023_processor2_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='processor2',
            name='account_number',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
