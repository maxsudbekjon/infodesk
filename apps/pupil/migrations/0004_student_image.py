from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pupil", "0003_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="student-avatar"),
        ),
    ]
