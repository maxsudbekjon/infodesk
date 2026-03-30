from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("group", "0004_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="attendance",
            name="is_present",
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
    ]
