from __future__ import annotations

from django.db import transaction

from common import bootstrap_django, clean_text, parse_args


bootstrap_django()

from import_student import (
    DEFAULT_STUDENT_EXCEL_PATH,
    _sync_import_coin,
    _sync_import_group_membership,
    build_full_name,
    choose_primary_phone,
    detect_column_indexes,
    find_existing_student,
    find_teacher,
    load_student_sheets,
    normalize_coin,
    parse_day_and_time,
    row_value,
    select_group,
)


def import_student_coins(excel_path: str) -> None:
    sheets = load_student_sheets(excel_path)
    updated_count = 0
    skipped_count = 0

    for sheet in sheets:
        try:
            teacher = find_teacher(sheet["sheet_name"], sheet["title"], sheet["index"])
            column_indexes = detect_column_indexes(sheet["headers"])
            print(f"[SHEET] {sheet['sheet_name']} -> teacher_id={teacher.id}")
        except Exception as exc:
            skipped_count += len(sheet["rows"])
            print(
                f"[SKIPPED SHEET] {sheet['sheet_name']} teacher yoki header muammosi sabab o'tkazib yuborildi: {exc}"
            )
            continue

        for row in sheet["rows"]:
            try:
                with transaction.atomic():
                    values = list(row["values"])
                    full_name = build_full_name(
                        row_value(values, column_indexes["last_name"]),
                        row_value(values, column_indexes["first_name"]),
                    )
                    if not full_name:
                        skipped_count += 1
                        print(f"[SKIPPED] {sheet['sheet_name']} row={row['__excel_row__']} full_name bo'sh")
                        continue

                    raw_time = row_value(values, column_indexes["time"])
                    if clean_text(raw_time) is None:
                        skipped_count += 1
                        print(
                            f"[SKIPPED] {sheet['sheet_name']} row={row['__excel_row__']} "
                            f"DARS VAQTI bo'sh"
                        )
                        continue

                    try:
                        days_choice, start_lesson = parse_day_and_time(raw_time)
                    except ValueError as exc:
                        skipped_count += 1
                        print(
                            f"[SKIPPED] {sheet['sheet_name']} row={row['__excel_row__']} "
                            f"{exc}"
                        )
                        continue

                    try:
                        group = select_group(teacher, sheet["sheet_name"], sheet["title"], days_choice, start_lesson)
                    except ValueError as exc:
                        skipped_count += 1
                        print(
                            f"[SKIPPED] {sheet['sheet_name']} row={row['__excel_row__']} "
                            f"{exc}"
                        )
                        continue

                    phone_indexes = column_indexes["phone_indexes"]
                    primary_phone, _secondary_phone = choose_primary_phone(
                        *[row_value(values, phone_index) for phone_index in phone_indexes]
                    )
                    student = find_existing_student(None, full_name, primary_phone, group)
                    if not student:
                        skipped_count += 1
                        print(
                            f"[SKIPPED] {sheet['sheet_name']} row={row['__excel_row__']} "
                            f"student topilmadi: {full_name}"
                        )
                        continue

                    coin = normalize_coin(row_value(values, column_indexes["coin"]))
                    _sync_import_group_membership(student, group)
                    _sync_import_coin(student, group, coin)
                    student.refresh_from_db(fields=["total_coin"])

                    updated_count += 1
                    print(
                        f"[UPDATED] coin row={row['__excel_row__']} "
                        f"name={full_name} coin={coin} total_coin={student.available_coin}"
                    )
            except Exception as exc:
                skipped_count += 1
                print(
                    f"[SKIPPED] {sheet['sheet_name']} row={row['__excel_row__']} "
                    f"kutilmagan xato: {exc}"
                )

    print(f"Student coin import yakunlandi. updated={updated_count}, skipped={skipped_count}")


if __name__ == "__main__":
    args = parse_args("Import student coins from CRM.xlsx", DEFAULT_STUDENT_EXCEL_PATH)
    excel_path = args.excel_path or DEFAULT_STUDENT_EXCEL_PATH
    import_student_coins(excel_path)
