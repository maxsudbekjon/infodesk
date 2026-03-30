from __future__ import annotations

from django.db import transaction

from common import (
    bootstrap_django,
    clean_text,
    first_row_reference,
    load_sheet_rows,
    parse_args,
    require_row,
    row_map,
)


bootstrap_django()

from apps.group.models import CourseTemplate
from apps.settings.models import Organization


def import_course_templates(excel_path: str) -> None:
    course_rows = load_sheet_rows(excel_path, "CourseTemplate")
    center_rows = row_map(load_sheet_rows(excel_path, "cennter"))
    created_count = 0
    updated_count = 0

    with transaction.atomic():
        for row in course_rows:
            center_ref = first_row_reference(row.get("markaz"))
            if center_ref is None:
                raise ValueError(f"CourseTemplate sheet {row['__row__']}-qatorda markaz reference yo'q.")

            center_row = require_row(center_rows, center_ref, "cennter")
            center_name = clean_text(center_row.get("name"))
            center = Organization.objects.filter(name=center_name).first()
            if not center:
                raise ValueError(
                    f"Organization topilmadi. Avval import_organization.py ni ishga tushiring. name={center_name}"
                )

            name = clean_text(row.get("kurs nomi"))
            duration_months = int(row.get("kurs davomiyligi") or 1)
            if not name:
                raise ValueError(f"CourseTemplate sheet {row['__row__']}-qatorda kurs nomi yo'q.")

            course, created = CourseTemplate.objects.update_or_create(
                center=center,
                name=name,
                defaults={"duration_months": duration_months},
            )

            if created:
                created_count += 1
                print(f"[CREATED] course row={row['__row__']} name={course.name}")
            else:
                updated_count += 1
                print(f"[UPDATED] course row={row['__row__']} name={course.name}")

    print(f"CourseTemplate import yakunlandi. created={created_count}, updated={updated_count}")


if __name__ == "__main__":
    args = parse_args("Import course templates from Excel")
    import_course_templates(args.excel_path)
