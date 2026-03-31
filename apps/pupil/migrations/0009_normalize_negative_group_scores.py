from django.db import migrations
from django.db.models import Sum


IMPORT_SCORE_REASON = "CRM-2.xlsx import coin"


def normalize_negative_group_scores(apps, schema_editor):
    GroupScore = apps.get_model("group", "GroupScore")
    Student = apps.get_model("pupil", "Student")

    student_ids = list(
        GroupScore.objects.filter(score__lt=0).values_list("student_id", flat=True).distinct()
    )
    if not student_ids:
        return

    GroupScore.objects.filter(score__lt=0).update(score=0)

    for student in Student.objects.filter(id__in=student_ids).only("id", "coin_offset", "used_coin"):
        earned_coin = (
            GroupScore.objects.filter(student_id=student.id)
            .exclude(reason=IMPORT_SCORE_REASON)
            .aggregate(total_coin=Sum("score"))
            .get("total_coin")
            or 0
        )
        student.total_coin = max(
            int(student.coin_offset or 0) + int(earned_coin) - int(student.used_coin or 0),
            0,
        )
        student.save(update_fields=["total_coin"])


class Migration(migrations.Migration):

    dependencies = [
        ("pupil", "0008_student_coin_offset"),
        ("group", "0005_attendance_is_present_nullable"),
    ]

    operations = [
        migrations.RunPython(normalize_negative_group_scores, migrations.RunPython.noop),
    ]
