from django.db import migrations, models
import django.db.models.deletion


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
        ("group", "0007_merge_20260407_1703"),
        ("pupil", "0010_merge_20260407_1703"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="group.group",
            ),
        ),
        migrations.RunPython(
            restore_student_group_from_m2m,
            reverse_code=noop_reverse,
        ),
    ]
