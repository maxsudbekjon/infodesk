from __future__ import annotations

from django.db import transaction

from common import (
    bootstrap_django,
    clean_text,
    first_row_reference,
    load_sheet_rows,
    normalize_date,
    normalize_days_choice,
    normalize_phone_number,
    normalize_time,
    parse_args,
    require_row,
    row_map,
)


bootstrap_django()

from apps.group.models import CourseTemplate, Group
from apps.settings.models import Branch, Organization
from apps.teacher.models import Teacher


def import_groups(excel_path: str) -> None:
    group_rows = load_sheet_rows(excel_path, "Group")
    course_rows = row_map(load_sheet_rows(excel_path, "CourseTemplate"))
    branch_rows = row_map(load_sheet_rows(excel_path, "branch"))
    teacher_rows = row_map(load_sheet_rows(excel_path, "Teacher"))
    center_rows = row_map(load_sheet_rows(excel_path, "cennter"))
    created_count = 0
    updated_count = 0

    with transaction.atomic():
        for row in group_rows:
            course_ref = first_row_reference(row.get("kurs id"))
            branch_ref = first_row_reference(row.get("filial id"))
            teacher_ref = first_row_reference(row.get("teacher id"))

            if course_ref is None or branch_ref is None or teacher_ref is None:
                raise ValueError(
                    f"Group sheet {row['__row__']}-qatorda kurs id, filial id yoki teacher id yetishmayapti."
                )

            branch_row = require_row(branch_rows, branch_ref, "branch")
            organization_ref = first_row_reference(branch_row.get("organization"))
            center_row = require_row(center_rows, organization_ref, "cennter")

            organization_name = clean_text(center_row.get("name"))
            organization = Organization.objects.filter(name=organization_name).first()
            if not organization:
                raise ValueError(
                    f"Organization topilmadi. Avval import_organization.py ni ishga tushiring. name={organization_name}"
                )

            branch_name = clean_text(branch_row.get("name"))
            branch = Branch.objects.filter(organization=organization, name=branch_name).first()
            if not branch:
                raise ValueError(
                    f"Branch topilmadi. Avval import_branch.py ni ishga tushiring. name={branch_name}"
                )

            course_row = require_row(course_rows, course_ref, "CourseTemplate")
            course_name = clean_text(course_row.get("kurs nomi"))
            course = CourseTemplate.objects.filter(center=organization, name=course_name).first()
            if not course:
                raise ValueError(
                    f"CourseTemplate topilmadi. Avval import_course_template.py ni ishga tushiring. name={course_name}"
                )

            teacher_row = require_row(teacher_rows, teacher_ref, "Teacher")
            teacher_phone = normalize_phone_number(teacher_row.get("phone_number"))
            teacher = Teacher.objects.filter(user__phone_number=teacher_phone).first()
            if not teacher:
                raise ValueError(
                    f"Teacher topilmadi. Avval import_teacher.py ni ishga tushiring. phone={teacher_phone}"
                )

            title = clean_text(row.get("guruh nomi"))
            if not title:
                raise ValueError(f"Group sheet {row['__row__']}-qatorda guruh nomi yo'q.")

            group, created = Group.objects.update_or_create(
                branch=branch,
                title=title,
                defaults={
                    "course": course,
                    "teacher": teacher,
                    "lessons_days_choice": normalize_days_choice(row.get("dars kunlari")),
                    "start_lesson": normalize_time(row.get("start_lesson")),
                    "end_lesson": normalize_time(row.get("end_lesson")),
                    "started_at": normalize_date(row.get("kurs boshlanish sanasi")),
                    "status": "active",
                },
            )

            if created:
                created_count += 1
                print(f"[CREATED] group row={row['__row__']} title={group.title}")
            else:
                updated_count += 1
                print(f"[UPDATED] group row={row['__row__']} title={group.title}")

    print(f"Group import yakunlandi. created={created_count}, updated={updated_count}")


if __name__ == "__main__":
    args = parse_args("Import groups from Excel")
    import_groups(args.excel_path)
