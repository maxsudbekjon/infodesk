from __future__ import annotations

from django.db import transaction

from common import (
    bootstrap_django,
    clean_text,
    first_row_reference,
    load_sheet_rows,
    normalize_decimal,
    normalize_phone_number,
    parse_args,
    parse_row_references,
    require_row,
    row_map,
)


bootstrap_django()

from apps.group.models import CourseTemplate
from apps.settings.models import Branch, Organization


def import_branches(excel_path: str) -> None:
    branch_rows = load_sheet_rows(excel_path, "branch")
    center_rows = row_map(load_sheet_rows(excel_path, "cennter"))
    course_rows = row_map(load_sheet_rows(excel_path, "CourseTemplate"))
    created_count = 0
    updated_count = 0

    with transaction.atomic():
        for row in branch_rows:
            organization_ref = first_row_reference(row.get("organization"))
            if organization_ref is None:
                raise ValueError(f"branch sheet {row['__row__']}-qatorda organization reference yo'q.")

            center_row = require_row(center_rows, organization_ref, "cennter")
            organization_name = clean_text(center_row.get("name"))
            organization = Organization.objects.filter(name=organization_name).first()
            if not organization:
                raise ValueError(
                    f"Organization topilmadi. Avval import_organization.py ni ishga tushiring. name={organization_name}"
                )

            name = clean_text(row.get("name"))
            if not name:
                raise ValueError(f"branch sheet {row['__row__']}-qatorda name yo'q.")

            defaults = {
                "phone": normalize_phone_number(row.get("phone")) or "",
                "address": clean_text(row.get("address")) or "",
                "latitude": normalize_decimal(row.get("latitude")),
                "longitude": normalize_decimal(row.get("longitude")),
                "is_active": True,
            }

            branch, created = Branch.objects.update_or_create(
                organization=organization,
                name=name,
                defaults=defaults,
            )

            course_ids = []
            for course_ref in parse_row_references(row.get("courses")):
                course_row = require_row(course_rows, course_ref, "CourseTemplate")
                course_name = clean_text(course_row.get("kurs nomi"))
                course = CourseTemplate.objects.filter(center=organization, name=course_name).first()
                if not course:
                    raise ValueError(
                        f"CourseTemplate topilmadi. Avval import_course_template.py ni ishga tushiring. name={course_name}"
                    )
                course_ids.append(course.id)

            if course_ids:
                branch.courses.set(CourseTemplate.objects.filter(id__in=course_ids))

            if created:
                created_count += 1
                print(f"[CREATED] branch row={row['__row__']} name={branch.name}")
            else:
                updated_count += 1
                print(f"[UPDATED] branch row={row['__row__']} name={branch.name}")

    print(f"Branch import yakunlandi. created={created_count}, updated={updated_count}")


if __name__ == "__main__":
    args = parse_args("Import branches from Excel")
    import_branches(args.excel_path)
