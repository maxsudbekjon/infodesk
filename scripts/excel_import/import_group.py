from __future__ import annotations

import re

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


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_key(value: str | None) -> str:
    if not value:
        return ""
    lowered = normalize_spaces(value).lower()
    lowered = lowered.replace("o'", "o").replace("g'", "g").replace("sh", "s")
    lowered = lowered.replace("’", "").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "", lowered)


def extract_teacher_hint_from_title(title: str | None) -> str | None:
    if not title or "/" not in title:
        return None
    tail = title.split("/")[-1].strip()
    tail = re.sub(r"\s+[ds]\s*/?\s*\d+$", "", tail, flags=re.IGNORECASE)
    tail = re.sub(r"\s+[ds]\d+$", "", tail, flags=re.IGNORECASE)
    return clean_text(tail)


def resolve_teacher(branch: Branch, title: str, teacher_phone: str | None) -> Teacher | None:
    phone_teacher = None
    if teacher_phone:
        phone_teacher = Teacher.objects.filter(user__phone_number=teacher_phone).first()

    teacher_hint = extract_teacher_hint_from_title(title)
    if not teacher_hint:
        return phone_teacher

    hint_key = normalize_key(teacher_hint)
    candidates = list(Teacher.objects.select_related("user").filter(branch=branch).order_by("id"))
    for teacher in candidates:
        full_name = clean_text(getattr(teacher.user, "full_name", "")) or ""
        teacher_tokens = [normalize_key(token) for token in full_name.split()]
        if hint_key and hint_key in teacher_tokens:
            if phone_teacher and phone_teacher.id != teacher.id:
                print(
                    f"[WARN] Group title bo'yicha teacher tuzatildi: title={title!r}, "
                    f"phone_teacher_id={phone_teacher.id}, matched_teacher_id={teacher.id}"
                )
            return teacher

    return phone_teacher


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

            title = clean_text(row.get("guruh nomi"))
            if not title:
                raise ValueError(f"Group sheet {row['__row__']}-qatorda guruh nomi yo'q.")

            teacher_row = require_row(teacher_rows, teacher_ref, "Teacher")
            teacher_phone = normalize_phone_number(teacher_row.get("phone_number"))
            teacher = resolve_teacher(branch, title, teacher_phone)
            if not teacher:
                raise ValueError(
                    f"Teacher topilmadi. Avval import_teacher.py ni ishga tushiring. "
                    f"phone={teacher_phone}, title={title}"
                )

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
