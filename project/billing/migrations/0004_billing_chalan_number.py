# Generated by Django 5.1.7 on 2025-03-08 03:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_billing_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='billing',
            name='chalan_number',
            field=models.CharField(default=12345, max_length=100),
            preserve_default=False,
        ),
    ]
