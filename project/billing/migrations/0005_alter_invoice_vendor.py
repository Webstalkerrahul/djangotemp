# Generated by Django 5.1.7 on 2025-07-08 02:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0004_invoice_pdf'),
        ('vendor', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='vendor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='vendor.vendor'),
        ),
    ]
