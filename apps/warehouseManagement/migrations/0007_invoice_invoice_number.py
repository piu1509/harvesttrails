# Generated by Django 5.0.6 on 2025-01-22 05:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouseManagement', '0006_alter_customer_available_credit'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='invoice_number',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
