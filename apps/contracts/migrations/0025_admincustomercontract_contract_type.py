# Generated by Django 5.0.6 on 2024-09-08 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0024_remove_admincustomercontract_amount_unit_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='admincustomercontract',
            name='contract_type',
            field=models.CharField(choices=[('Single Crop', 'Single Crop'), ('Multiple Crop', 'Multiple Crop')], default='Single Crop', max_length=25),
        ),
    ]
