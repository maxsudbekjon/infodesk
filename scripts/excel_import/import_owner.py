from __future__ import annotations

from django.db import transaction

from common import (
    bootstrap_django,
    clean_text,
    default_password,
    load_sheet_rows,
    normalize_owner_role,
    normalize_phone_number,
    parse_args,
)


bootstrap_django()

from apps.user.models import User


def import_owners(excel_path: str) -> None:
    rows = load_sheet_rows(excel_path, "owner")
    created_count = 0
    updated_count = 0

    with transaction.atomic():
        for row in rows:
            full_name = clean_text(row.get("full_name"))
            phone_number = normalize_phone_number(row.get("phone_number"))
            role = normalize_owner_role(row.get("role"))

            if not phone_number:
                raise ValueError(f"owner sheet {row['__row__']}-qatorda phone_number yo'q.")

            user = User.objects.filter(phone_number=phone_number).first()
            if not user:
                user = User.objects.create_user(
                    phone_number=phone_number,
                    password=default_password(phone_number),
                    full_name=full_name,
                    role=role,
                )
                created_count += 1
                print(f"[CREATED] owner row={row['__row__']} phone={phone_number}")
                continue

            update_fields = []
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                update_fields.append("full_name")
            if user.role != role:
                user.role = role
                update_fields.append("role")

            if update_fields:
                user.save(update_fields=update_fields)
                updated_count += 1
                print(f"[UPDATED] owner row={row['__row__']} phone={phone_number}")
            else:
                print(f"[SKIPPED] owner row={row['__row__']} phone={phone_number}")

    print(f"Owner import yakunlandi. created={created_count}, updated={updated_count}")


if __name__ == "__main__":
    args = parse_args("Import owner users from Excel")
    import_owners(args.excel_path)
