# Generated by Django 5.0.6 on 2024-09-06 10:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0019_remove_admincustomercontract_tax_percentage_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adminprocessorcontract',
            name='amount_unit',
        ),
        migrations.RemoveField(
            model_name='adminprocessorcontract',
            name='contract_amount',
        ),
        migrations.RemoveField(
            model_name='adminprocessorcontract',
            name='crop',
        ),
        migrations.RemoveField(
            model_name='adminprocessorcontract',
            name='crop_type',
        ),
        migrations.RemoveField(
            model_name='adminprocessorcontract',
            name='per_unit_rate',
        ),
        migrations.AddField(
            model_name='adminprocessorcontract',
            name='contract_type',
            field=models.CharField(choices=[('Single Crop', 'Single Crop'), ('Multiple Crop', 'Multiple Crop')], default='Single Crop', max_length=25),
        ),
        migrations.CreateModel(
            name='CropDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('crop', models.CharField(choices=[('RICE', 'Rice'), ('WHEAT', 'Wheat'), ('PEANUT', 'Peanut'), ('BEANS', 'Beans')], max_length=10)),
                ('crop_type', models.CharField(blank=True, max_length=255, null=True)),
                ('contract_amount', models.PositiveBigIntegerField()),
                ('amount_unit', models.CharField(choices=[('LBS', 'LBS'), ('MT', 'MT')], max_length=10)),
                ('per_unit_rate', models.CharField(blank=True, max_length=255, null=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contractCrop', to='contracts.adminprocessorcontract')),
            ],
        ),
    ]
