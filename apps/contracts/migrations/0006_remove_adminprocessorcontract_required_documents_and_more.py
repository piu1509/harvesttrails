# Generated by Django 5.0.6 on 2024-08-22 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0005_adminprocessorcontract_is_signed_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adminprocessorcontract',
            name='required_documents',
        ),
        migrations.AddField(
            model_name='adminprocessorcontractdocuments',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
