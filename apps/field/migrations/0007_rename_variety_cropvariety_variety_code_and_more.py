# Generated by Django 5.0.6 on 2024-09-27 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('field', '0006_alter_field_variety_alter_fieldupdated_variety_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cropvariety',
            old_name='variety',
            new_name='variety_code',
        ),
        migrations.AddField(
            model_name='cropvariety',
            name='variety_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
