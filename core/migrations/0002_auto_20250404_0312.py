from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='budget',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='budget',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='budget',
            name='period',
            field=models.CharField(choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], default='monthly', max_length=20),
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.CharField(choices=[('USD', 'US Dollar ($)'), ('EUR', 'Euro (€)'), ('GBP', 'British Pound (£)'), ('JPY', 'Japanese Yen (¥)'), ('INR', 'Indian Rupee (₹)')], default='USD', max_length=3)),
                ('theme', models.CharField(choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System Default')], default='system', max_length=10)),
                ('notifications_enabled', models.BooleanField(default=True)),
                ('email_notifications', models.BooleanField(default=True)),
                ('budget_alerts', models.BooleanField(default=True)),
                ('goal_reminders', models.BooleanField(default=True)),
                ('language', models.CharField(default='en', max_length=10)),
                ('timezone', models.CharField(default='UTC', max_length=50)),
                ('date_format', models.CharField(default='%Y-%m-%d', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
            options={
                'verbose_name_plural': 'Settings',
            },
        ),
    ] 