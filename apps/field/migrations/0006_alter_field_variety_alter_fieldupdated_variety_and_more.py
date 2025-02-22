# Generated by Django 5.0.6 on 2024-09-27 05:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('field', '0005_alter_fieldupdated_crop'),
    ]

    operations = [
        migrations.AlterField(
            model_name='field',
            name='variety',
            field=models.CharField(blank=True, choices=[('DG-263L', 'DG-263L'), ('DG-Wheat', 'DG-Wheat'), ('DG3605', 'DG3605'), ('DG 1464', 'DG 1464'), ('DG 2425 XF', 'DG 2425 XF'), ('DG 3215 B3XF', 'DG 3215 B3XF'), ('DG 3450 B2XF', 'DG 3450 B2XF'), ('DG 3470 B3XF', 'DG 3470 B3XF'), ('DG 3570 B3XF', 'DG 3570 B3XF'), ('DG 3635 B2XF', 'DG 3635 B2XF'), ('DG 3544 B2XF', 'DG 3544 B2XF'), ('DG 3651NR B2XF', 'DG 3651NR B2XF'), ('DG 3109 B2XF', 'DG 3109 B2XF'), ('DG 3387 B3XF', 'DG 3387 B3XF'), ('DG 3421 B3XF', 'DG 3421 B3XF'), ('DG H929 B3XF', 'DG H929 B3XF'), ('DG 3555 B3XF', 'DG 3555 B3XF'), ('DG 3402 B3XF', 'DG 3402 B3XF'), ('DG H959 B3XF', 'DG H959 B3XF'), ('DG 3469 B3XF', 'DG 3469 B3XF'), ('DG 3615 B3XF', 'DG 3615 B3XF'), ('DG P224 B3XF', 'DG P224 B3XF'), ('DG 3385 B2XF', 'DG 3385 B2XF'), ('DG 3422 B3XF', 'DG 3422 B3XF'), ('DG 3799 B3XF', 'DG 3799 B3XF'), ('DG 1000 B1XF', 'DG 1000 B1XF')], max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='fieldupdated',
            name='variety',
            field=models.CharField(blank=True, choices=[('DG-263L', 'DG-263L'), ('DG-Wheat', 'DG-Wheat'), ('DG3605', 'DG3605'), ('DG 1464', 'DG 1464'), ('DG 2425 XF', 'DG 2425 XF'), ('DG 3215 B3XF', 'DG 3215 B3XF'), ('DG 3450 B2XF', 'DG 3450 B2XF'), ('DG 3470 B3XF', 'DG 3470 B3XF'), ('DG 3570 B3XF', 'DG 3570 B3XF'), ('DG 3635 B2XF', 'DG 3635 B2XF'), ('DG 3544 B2XF', 'DG 3544 B2XF'), ('DG 3651NR B2XF', 'DG 3651NR B2XF'), ('DG 3109 B2XF', 'DG 3109 B2XF'), ('DG 3387 B3XF', 'DG 3387 B3XF'), ('DG 3421 B3XF', 'DG 3421 B3XF'), ('DG H929 B3XF', 'DG H929 B3XF'), ('DG 3555 B3XF', 'DG 3555 B3XF'), ('DG 3402 B3XF', 'DG 3402 B3XF'), ('DG H959 B3XF', 'DG H959 B3XF'), ('DG 3469 B3XF', 'DG 3469 B3XF'), ('DG 3615 B3XF', 'DG 3615 B3XF'), ('DG P224 B3XF', 'DG P224 B3XF'), ('DG 3385 B2XF', 'DG 3385 B2XF'), ('DG 3422 B3XF', 'DG 3422 B3XF'), ('DG 3799 B3XF', 'DG 3799 B3XF'), ('DG 1000 B1XF', 'DG 1000 B1XF')], max_length=255, null=True),
        ),
        migrations.CreateModel(
            name='CropVariety',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variety', models.CharField(blank=True, max_length=255, null=True)),
                ('crop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cropVariety', to='field.crop')),
            ],
        ),
    ]
