# Generated by Django 5.0.6 on 2024-08-21 08:02

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminProcessorContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('processor_id', models.CharField(max_length=255)),
                ('processor_type', models.CharField(choices=[('T1', 'T1'), ('T2', 'T2'), ('T3', 'T3'), ('T4', 'T4')], max_length=5)),
                ('crop', models.CharField(choices=[('RICE', 'Rice'), ('COTTON', 'Cotton'), ('WHEAT', 'Wheat'), ('PEANUT', 'Peanut'), ('BEANS', 'Beans')], max_length=10)),
                ('contract_amount', models.PositiveBigIntegerField()),
                ('amount_unit', models.CharField(choices=[('LBS', 'LBS'), ('MT', 'MT')], max_length=10)),
                ('total_price', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('contract_start_date', models.DateTimeField()),
                ('contract_period', models.PositiveIntegerField(choices=[('Days', 'Days'), ('Months', 'Months'), ('Year', 'Year')], default='Days', help_text='Warranty period')),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Active', 'Active'), ('Completed', 'Completed'), ('Terminated', 'Terminated')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('required_documents', models.TextField(blank=True, help_text='List of required documents, separated by commas')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contractingUser', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AdminProcessorContractDocuments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document', models.FileField(upload_to='contracts/documents/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contractDocuments', to='contracts.adminprocessorcontract')),
            ],
        ),
        migrations.CreateModel(
            name='AdminProcessorContractSignature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signed_at', models.DateTimeField(auto_now_add=True)),
                ('signature', models.TextField(help_text='A textual or digital representation of the signature')),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contractSignatures', to='contracts.adminprocessorcontract')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signingUser', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
