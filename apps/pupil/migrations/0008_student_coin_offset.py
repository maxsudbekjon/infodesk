from django.db import migrations, models
from django.db.models import Sum


IMPORT_SCORE_REASON = "CRM-2.xlsx import coin"


def populate_student_coin_offset(apps, schema_editor):
    Student = apps.get_model("pupil", "Student")
    GroupScore = apps.get_model("group", "GroupScore")

    for student in Student.objects.all().only("id", "used_coin", "total_coin"):
        earned_coin = (
            GroupScore.objects.filter(student_id=student.id)
            .exclude(reason=IMPORT_SCORE_REASON)
            .aggregate(total_coin=Sum("score"))
            .get("total_coin")
            or 0
        )
        student.coin_offset = int(student.total_coin or 0) + int(student.used_coin or 0) - int(earned_coin)
        student.save(update_fields=["coin_offset"])

    GroupScore.objects.filter(reason=IMPORT_SCORE_REASON).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pupil", "0007_student_total_coin"),
        ("group", "0005_attendance_is_present_nullable"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="coin_offset",
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(populate_student_coin_offset, migrations.RunPython.noop),
    ]
