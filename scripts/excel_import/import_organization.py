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
    require_row,
    row_map,
)


bootstrap_django()

from apps.settings.models import Organization
from apps.user.models import User


def import_organizations(excel_path: str) -> None:
    center_rows = load_sheet_rows(excel_path, "cennter")
    owner_rows = row_map(load_sheet_rows(excel_path, "owner"))
    created_count = 0
    updated_count = 0

    with transaction.atomic():
        for row in center_rows:
            owner_ref = first_row_reference(row.get("owner"))
            if owner_ref is None:
                raise ValueError(f"cennter sheet {row['__row__']}-qatorda owner reference yo'q.")

            owner_row = require_row(owner_rows, owner_ref, "owner")
            owner_phone = normalize_phone_number(owner_row.get("phone_number"))
            owner = User.objects.filter(phone_number=owner_phone).first()
            if not owner:
                raise ValueError(
                    f"Owner topilmadi. Avval import_owner.py ni ishga tushiring. phone={owner_phone}"
                )

            name = clean_text(row.get("name"))
            if not name:
                raise ValueError(f"cennter sheet {row['__row__']}-qatorda name yo'q.")

            defaults = {
                "organization_phone": normalize_phone_number(row.get("oragnization_phone")),
                "latitude": normalize_decimal(row.get("latitude")),
                "longitude": normalize_decimal(row.get("longitude")),
                "address": clean_text(row.get("address")) or "",
            }

            organization, created = Organization.objects.update_or_create(
                owner=owner,
                name=name,
                defaults=defaults,
            )

            if created:
                created_count += 1
                print(f"[CREATED] organization row={row['__row__']} name={organization.name}")
            else:
                updated_count += 1
                print(f"[UPDATED] organization row={row['__row__']} name={organization.name}")

    print(f"Organization import yakunlandi. created={created_count}, updated={updated_count}")


if __name__ == "__main__":
    args = parse_args("Import organizations from Excel")
    import_organizations(args.excel_path)
