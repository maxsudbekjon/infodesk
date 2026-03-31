from django.db import migrations, models
from django.db.models import Sum


def populate_student_total_coin(apps, schema_editor):
    Student = apps.get_model("pupil", "Student")
    GroupScore = apps.get_model("group", "GroupScore")

    for student in Student.objects.all().only("id", "used_coin"):
        earned_coin = (
            GroupScore.objects.filter(student_id=student.id).aggregate(total_coin=Sum("score")).get("total_coin")
            or 0
        )
        student.total_coin = max(int(earned_coin) - int(student.used_coin or 0), 0)
        student.save(update_fields=["total_coin"])


class Migration(migrations.Migration):

    dependencies = [
        ("group", "0005_attendance_is_present_nullable"),
        ("pupil", "0006_student_contract"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="total_coin",
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(populate_student_total_coin, migrations.RunPython.noop),
    ]
