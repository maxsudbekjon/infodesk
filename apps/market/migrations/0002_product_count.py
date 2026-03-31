from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
