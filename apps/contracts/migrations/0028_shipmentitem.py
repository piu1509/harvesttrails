# Generated by Django 5.0.6 on 2024-10-17 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0027_alter_cropdetails_crop_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShipmentItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=255)),
                ('item_type', models.CharField(max_length=255)),
                ('quickbooks_id', models.CharField(max_length=255, unique=True)),
                ('per_unit_price', models.DecimalField(decimal_places=3, max_digits=10)),
                ('description', models.TextField(blank=True, null=True)),
                ('type', models.CharField(choices=[('Service', 'Service'), ('Inventory', 'Inventory'), ('NonInventory', 'NonInventory')], default='Inventory', max_length=255)),
                ('purchase_price', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('purchase_description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
    ]
