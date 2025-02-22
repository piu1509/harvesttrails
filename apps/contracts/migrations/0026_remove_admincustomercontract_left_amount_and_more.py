# Generated by Django 5.0.6 on 2024-09-10 05:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0025_admincustomercontract_contract_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='admincustomercontract',
            name='left_amount',
        ),
        migrations.AlterField(
            model_name='admincustomercontract',
            name='contract_start_date',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='admincustomercontract',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='adminprocessorcontract',
            name='contract_start_date',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='adminprocessorcontract',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='cropdetails',
            name='contract_amount',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='cropdetails',
            name='left_amount',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='cropdetails',
            name='per_unit_rate',
            field=models.DecimalField(decimal_places=3, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customercontractcropdetails',
            name='contract_amount',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='customercontractcropdetails',
            name='left_amount',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customercontractcropdetails',
            name='per_unit_rate',
            field=models.DecimalField(decimal_places=3, default=1, max_digits=10),
            preserve_default=False,
        ),
    ]
