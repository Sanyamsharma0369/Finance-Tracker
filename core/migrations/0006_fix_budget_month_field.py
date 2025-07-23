from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_add_timestamps_to_models'),
    ]

    operations = [
        # Make the month field nullable
        migrations.AlterField(
            model_name='budget',
            name='month',
            field=models.DateField(null=True, blank=True),
        ),
    ] 