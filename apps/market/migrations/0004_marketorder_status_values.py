from django.db import migrations, models


def forwards(apps, schema_editor):
    MarketOrder = apps.get_model("market", "MarketOrder")
    MarketOrder.objects.filter(status="pending").update(status="created")
    MarketOrder.objects.filter(status="completed").update(status="delivered")


def backwards(apps, schema_editor):
    MarketOrder = apps.get_model("market", "MarketOrder")
    MarketOrder.objects.filter(status="created").update(status="pending")
    MarketOrder.objects.filter(status="delivered").update(status="completed")


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0003_marketorder_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="marketorder",
            name="status",
            field=models.CharField(
                choices=[
                    ("created", "Created"),
                    ("delivered", "Delivered"),
                    ("cancelled", "Cancelled"),
                ],
                default="created",
                max_length=20,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
