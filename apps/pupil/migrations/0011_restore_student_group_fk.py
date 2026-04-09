from django.db import migrations


def restore_student_group_from_m2m(apps, schema_editor):
    Student = apps.get_model("pupil", "Student")
    Group = apps.get_model("group", "Group")

    for student in Student.objects.filter(group__isnull=True).iterator():
        related_groups = (
            Group.objects.filter(students=student)
            .order_by(
                "-status",
                "-created_at",
                "-id",
            )
        )
        selected_group = related_groups.first()
        if selected_group is None:
            continue

        Student.objects.filter(pk=student.pk).update(group_id=selected_group.pk)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("pupil", "0011_rename_studenttransfer_studnettransfer_student_group"),
    ]

    operations = [
        migrations.RunPython(
            restore_student_group_from_m2m,
            reverse_code=noop_reverse,
        ),
    ]
