from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pupil", "0005_student_used_coin"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="contract",
            field=models.BooleanField(default=False),
        ),
    ]
