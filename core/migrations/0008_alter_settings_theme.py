# Generated by Django 5.2 on 2025-04-04 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_otp_alter_category_options_alter_transaction_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='settings',
            name='theme',
            field=models.CharField(choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System Default')], default='dark', max_length=10),
        ),
    ]
