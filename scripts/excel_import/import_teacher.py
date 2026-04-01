from __future__ import annotations

from django.db import transaction

from apps.user.models.user import split_full_name_parts
from common import (
    bootstrap_django,
    clean_text,
    default_password,
    first_row_reference,
    load_sheet_rows,
    normalize_phone_number,
    parse_args,
    require_row,
    row_map,
)


bootstrap_django()

from apps.settings.models import Branch, Organization
from apps.teacher.models import Teacher
from apps.user.models import User


def extract_teacher_full_name(row: dict) -> str | None:
    for key in ("ism familiya", "ism familya", "full_name", "teacher_name", "name"):
        full_name = clean_text(row.get(key))
        if full_name:
            return full_name
    return None


def build_name_fields(full_name: str | None) -> dict[str, str]:
    if not full_name:
        return {}

    first_name, last_name = split_full_name_parts(full_name)
    return {
        "full_name": full_name,
        "first_name": first_name,
        "last_name": last_name,
    }


def import_teachers(excel_path: str) -> None:
    teacher_rows = load_sheet_rows(excel_path, "Teacher")
    branch_rows = row_map(load_sheet_rows(excel_path, "branch"))
    center_rows = row_map(load_sheet_rows(excel_path, "cennter"))
    created_count = 0
    updated_count = 0

    with transaction.atomic():
        for row in teacher_rows:
            branch_ref = first_row_reference(row.get("filial id"))
            if branch_ref is None:
                raise ValueError(f"Teacher sheet {row['__row__']}-qatorda filial id yo'q.")

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

            phone_number = normalize_phone_number(row.get("phone_number"))
            full_name = extract_teacher_full_name(row)
            if not phone_number:
                raise ValueError(f"Teacher sheet {row['__row__']}-qatorda phone_number yo'q.")

            name_fields = build_name_fields(full_name)
            user = User.objects.filter(phone_number=phone_number).first()
            if not user:
                user = User.objects.create_user(
                    phone_number=phone_number,
                    password=default_password(phone_number),
                    role="teacher",
                    **name_fields,
                )
            else:
                user_updates = []
                for field_name, field_value in name_fields.items():
                    if getattr(user, field_name) != field_value:
                        setattr(user, field_name, field_value)
                        user_updates.append(field_name)
                if user.role != "teacher":
                    user.role = "teacher"
                    user_updates.append("role")
                if user_updates:
                    user.save(update_fields=user_updates)

            teacher, created = Teacher.objects.update_or_create(
                user=user,
                defaults={
                    "branch": branch,
                    "is_archived": False,
                },
            )

            if created:
                created_count += 1
                print(f"[CREATED] teacher row={row['__row__']} name={full_name}")
            else:
                updated_count += 1
                print(f"[UPDATED] teacher row={row['__row__']} name={full_name}")

    print(f"Teacher import yakunlandi. created={created_count}, updated={updated_count}")


if __name__ == "__main__":
    args = parse_args("Import teachers from Excel")
    import_teachers(args.excel_path)
