# Generated by Django 5.0.6 on 2024-09-27 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processor2', '0018_alter_processor_sku_processor_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipmentmanagement',
            name='crop',
            field=models.CharField(blank=True, max_length=155, null=True),
        ),
    ]
