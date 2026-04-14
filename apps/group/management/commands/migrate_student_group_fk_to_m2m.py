"""
One-time management command: copy Student.group FK relationships into the
Group.students M2M table and recalculate Group.total_student for all groups.

Run once after deploying the Phase-4a code changes:

    python manage.py migrate_student_group_fk_to_m2m
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.group.models.group import Group
from apps.pupil.models.student import Student


class Command(BaseCommand):
    help = "Back-fill Group.students M2M from Student.group FK and sync total_student counts."

    def handle(self, *args, **options):
        self.stdout.write("Step 1: back-filling M2M from FK …")

        students_with_fk = (
            Student.objects.exclude(group__isnull=True)
            .select_related("group")
            .only("id", "group_id")
        )

        migrated = 0
        for student in students_with_fk.iterator(chunk_size=500):
            if not student.groups.filter(pk=student.group_id).exists():
                student.groups.add(student.group)
                migrated += 1

        self.stdout.write(self.style.SUCCESS(f"  → {migrated} student(s) added to M2M."))

        self.stdout.write("Step 2: recalculating total_student for all groups …")
        updated = 0
        for group in Group.objects.iterator(chunk_size=200):
            count = group.students.exclude(status__in=["archived", "frozen"]).count()
            with transaction.atomic():
                Group.objects.filter(pk=group.pk).update(total_student=count)
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"  → {updated} group(s) updated."))
        self.stdout.write(self.style.SUCCESS("Done."))
