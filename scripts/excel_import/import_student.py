from __future__ import annotations

import re
from datetime import date, datetime, time

from django.db import transaction
from django.utils import timezone
from openpyxl import load_workbook

from common import (
    bootstrap_django,
    clean_text,
    default_password,
    extract_phone_number,
    parse_args,
)


bootstrap_django()

from apps.group.models import Group, GroupScore
from apps.pupil.models import Student
from apps.teacher.models import Teacher
from apps.user.models import User


DEFAULT_STUDENT_EXCEL_PATH = "/Users/maxsudtoshpulat/Downloads/CRM.xlsx"
CURRENT_YEAR_FOR_AGE = 2026
IMPORT_SCORE_REASON = "CRM.xlsx import coin"


def load_student_sheets(excel_path: str) -> list[dict]:
    workbook = load_workbook(excel_path, read_only=True, data_only=True)
    sheets = []

    for index, sheet_name in enumerate(workbook.sheetnames, start=1):
        worksheet = workbook[sheet_name]
        rows = list(worksheet.iter_rows(values_only=True))
        if len(rows) < 2:
            continue

        title = rows[0][0]
        headers = rows[1]
        data_rows = []
        for excel_row_number, row in enumerate(rows[2:], start=3):
            if not any(value not in (None, "") for value in row):
                continue
            data_rows.append({"__excel_row__": excel_row_number, "values": row})

        sheets.append(
            {
                "index": index,
                "sheet_name": sheet_name,
                "title": clean_text(title) or "",
                "headers": headers,
                "rows": data_rows,
            }
        )

    workbook.close()
    return sheets


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_key(value: str | None) -> str:
    if not value:
        return ""
    lowered = normalize_spaces(value).lower()
    lowered = lowered.replace("o'", "o").replace("g'", "g").replace("sh", "s")
    lowered = lowered.replace("’", "").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "", lowered)


def extract_header_phone(header_text: str) -> str | None:
    matches = re.findall(r"(?:\d[\s-]*){9,12}", header_text or "")
    for match in matches:
        phone = extract_phone_number(match)
        if phone:
            return phone
    return None


def teacher_fallback_by_sheet_order(sheet_index: int) -> Teacher | None:
    teachers = list(Teacher.objects.select_related("user").order_by("id"))
    if 1 <= sheet_index <= len(teachers):
        return teachers[sheet_index - 1]
    return None


def find_teacher(sheet_name: str, header_text: str, sheet_index: int) -> Teacher:
    phone = extract_header_phone(header_text)
    if phone:
        teacher = Teacher.objects.select_related("user").filter(user__phone_number=phone).first()
        if teacher:
            return teacher

    search_text = f"{sheet_name} {header_text}"
    search_key = normalize_key(search_text)
    teachers = list(Teacher.objects.select_related("user").all())
    scored: list[tuple[int, Teacher]] = []

    for teacher in teachers:
        full_name = getattr(teacher.user, "full_name", "") or getattr(teacher.user, "display_name", "")
        teacher_key = normalize_key(full_name)
        score = 0
        if teacher_key and teacher_key in search_key:
            score += 5
        teacher_tokens = [normalize_key(token) for token in normalize_spaces(full_name).split() if len(token) >= 3]
        for token in teacher_tokens:
            if token and token in search_key:
                score += 2

        if score:
            scored.append((score, teacher))

    if scored:
        scored.sort(key=lambda item: (-item[0], item[1].id))
        if len(scored) == 1 or scored[0][0] > scored[1][0]:
            return scored[0][1]

    fallback = teacher_fallback_by_sheet_order(sheet_index)
    if fallback:
        print(
            f"[WARN] Teacher aniq topilmadi, sheet tartibi bo'yicha fallback ishlatildi: "
            f"sheet={sheet_name!r} -> teacher_id={fallback.id}"
        )
        return fallback

    raise ValueError(f"Teacher topilmadi: sheet={sheet_name!r}, header={header_text!r}")


def parse_day_and_time(value: object) -> tuple[str, time]:
    text = normalize_spaces(str(value or "")).replace(";", ":")
    match = re.match(r"^(?P<prefix>[dDsS])\s*/?\s*(?P<time>\d{1,2}:\d{2})$", text)
    if not match:
        raise ValueError(f"VAQT formatini tushunib bo'lmadi: {value}")

    prefix = match.group("prefix").lower()
    if prefix == "d":
        days_choice = "odd_days"
    elif prefix == "s":
        days_choice = "even_days"
    else:
        raise ValueError(f"VAQT formatini tushunib bo'lmadi: {value}")

    parsed_time = datetime.strptime(match.group("time"), "%H:%M").time()
    return days_choice, parsed_time


def detect_column_indexes(headers: object) -> dict[str, object]:
    phone_indexes: list[int] = []
    contract_indexes: list[int] = []
    indexes: dict[str, object] = {
        "last_name": None,
        "first_name": None,
        "birthday": None,
        "arrival_date": None,
        "time": None,
        "coin": None,
        "phone_indexes": phone_indexes,
        "contract_indexes": contract_indexes,
    }

    for index, header in enumerate(headers or []):
        text = normalize_spaces(str(header or "")).lower()
        if "famili" in text or "family" in text or text.startswith("fam"):
            indexes["last_name"] = index
        elif text in {"ism", "ismi"} or text.endswith(" ism"):
            indexes["first_name"] = index
        elif "telefon" in text or "tel nomer" in text:
            phone_indexes.append(index)
        elif "birth" in text or "brith" in text:
            indexes["birthday"] = index
        elif "kelgan" in text:
            indexes["arrival_date"] = index
        elif "vaqt" in text:
            indexes["time"] = index
        elif "coin" in text:
            indexes["coin"] = index
        elif "shart" in text:
            contract_indexes.append(index)

    birthday_index = indexes["birthday"]
    if phone_indexes and birthday_index is not None:
        for extra_index in range(phone_indexes[-1] + 1, birthday_index):
            phone_indexes.append(extra_index)

    return indexes


def row_value(values: list[object], index: int | None):
    if index is None or index >= len(values):
        return None
    return values[index]


def time_distance_minutes(left: time, right: time) -> int:
    left_minutes = left.hour * 60 + left.minute
    right_minutes = right.hour * 60 + right.minute
    return abs(left_minutes - right_minutes)


def nearest_group_for_teacher(teacher: Teacher, days_choice: str, start_lesson: time) -> Group | None:
    candidates = list(
        Group.objects.select_related("course", "teacher__user", "branch")
        .filter(teacher=teacher, lessons_days_choice=days_choice)
        .order_by("start_lesson", "id")
    )
    if not candidates:
        return None

    ranked = sorted(
        candidates,
        key=lambda group: (
            time_distance_minutes(group.start_lesson, start_lesson),
            group.start_lesson > start_lesson,
            group.id,
        ),
    )
    nearest = ranked[0]
    if time_distance_minutes(nearest.start_lesson, start_lesson) <= 60:
        return nearest
    return None


def group_candidates_for_teacher(teacher: Teacher, days_choice: str, start_lesson: time) -> list[Group]:
    return list(
        Group.objects.select_related("course", "teacher__user", "branch")
        .filter(teacher=teacher, lessons_days_choice=days_choice, start_lesson=start_lesson)
        .order_by("id")
    )


def select_group(teacher: Teacher, sheet_name: str, header_text: str, days_choice: str, start_lesson: time) -> Group:
    candidates = group_candidates_for_teacher(teacher, days_choice, start_lesson)
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        sheet_key = f"{sheet_name} {header_text}"
        for candidate in candidates:
            candidate_key = normalize_key(
                f"{candidate.title} {candidate.course.name} {getattr(candidate.teacher.user, 'full_name', '')}"
            )
            if candidate_key and any(token and token in candidate_key for token in _interesting_tokens(sheet_key)):
                return candidate
        raise ValueError(
            f"Bir nechta group topildi: teacher_id={teacher.id}, days={days_choice}, start={start_lesson}"
        )

    nearest_teacher_group = nearest_group_for_teacher(teacher, days_choice, start_lesson)
    if nearest_teacher_group:
        print(
            f"[WARN] Exact group topilmadi, eng yaqin teacher group tanlandi: "
            f"sheet={sheet_name!r}, teacher_id={teacher.id}, requested={start_lesson}, "
            f"matched={nearest_teacher_group.start_lesson}, group={nearest_teacher_group.title}"
        )
        return nearest_teacher_group

    fallback_candidates = list(
        Group.objects.select_related("course", "teacher__user", "branch")
        .filter(lessons_days_choice=days_choice, start_lesson=start_lesson)
        .order_by("id")
    )
    sheet_tokens = _interesting_tokens(f"{sheet_name} {header_text}")
    for candidate in fallback_candidates:
        candidate_text = normalize_key(
            f"{candidate.title} {candidate.course.name} {getattr(candidate.teacher.user, 'full_name', '')}"
        )
        if any(token and token in candidate_text for token in sheet_tokens):
            return candidate

    raise ValueError(
        f"Group topilmadi: sheet={sheet_name!r}, teacher_id={teacher.id}, days={days_choice}, start={start_lesson}"
    )


def _interesting_tokens(normalized_text: str) -> list[str]:
    raw_tokens = re.findall(r"[a-z0-9]+", normalized_text)
    stopwords = {
        "ingliz",
        "tili",
        "foundation",
        "kids",
        "full",
        "web",
        "dasturlash",
        "grafik",
        "dizayn",
        "kiberxavfsizlik",
        "matematika",
        "rus",
        "smm",
        "ai",
        "opa",
    }
    return [token for token in raw_tokens if len(token) >= 3 and token not in stopwords]


def normalize_contract(value: object) -> bool:
    text = (clean_text(value) or "").lower()
    return text in {"bor", "shartnoma", "bor.", "shartnoma."}


def normalize_arrival_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        value = value.date()
    if not isinstance(value, date):
        raise ValueError(f"KELGAN SANA formatini tushunib bo'lmadi: {value}")

    year = 2026 if 1 <= value.month <= 3 else 2025
    return value.replace(year=year)


def normalize_birthday(value: object) -> date | None:
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    if isinstance(value, float) and value.is_integer():
        value = int(value)

    if isinstance(value, int):
        return date(CURRENT_YEAR_FOR_AGE - value, 1, 1)

    text = clean_text(value)
    if not text:
        return None
    if text.isdigit():
        return date(CURRENT_YEAR_FOR_AGE - int(text), 1, 1)
    return None


def normalize_coin(value: object) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, float):
        return int(value)
    return int(str(value))


def build_full_name(last_name: object, first_name: object) -> str:
    parts = [clean_text(last_name), clean_text(first_name)]
    return " ".join(part for part in parts if part)


def choose_primary_phone(*phone_values: object) -> tuple[str | None, str | None]:
    phones: list[str] = []
    for raw_value in phone_values:
        phone = extract_phone_number(raw_value)
        if phone and phone not in phones:
            phones.append(phone)

    primary_phone = phones[0] if phones else None
    secondary_phone = phones[1] if len(phones) > 1 else None
    return primary_phone, secondary_phone


def make_aware_midday(value: date | None):
    if value is None:
        return None
    naive = datetime.combine(value, time(12, 0))
    return timezone.make_aware(naive)


def upsert_student_user(full_name: str, primary_phone: str | None, secondary_phone: str | None, birthday: date | None):
    if not primary_phone:
        return None

    user = User.objects.filter(phone_number=primary_phone).first()
    if not user:
        user = User.objects.create_user(
            phone_number=primary_phone,
            password=default_password(primary_phone),
            full_name=full_name,
            role="student",
            birthday=birthday,
            phone_number2=secondary_phone,
        )
        return user

    update_fields = []
    if full_name and user.full_name != full_name:
        user.full_name = full_name
        update_fields.append("full_name")
    if user.role != "student":
        user.role = "student"
        update_fields.append("role")
    if birthday and user.birthday != birthday:
        user.birthday = birthday
        update_fields.append("birthday")
    if secondary_phone and secondary_phone != user.phone_number:
        secondary_busy = User.objects.filter(phone_number=secondary_phone).exclude(pk=user.pk).exists()
        other_user = User.objects.filter(phone_number2=secondary_phone).exclude(pk=user.pk).first()
        if not secondary_busy and not other_user and user.phone_number2 != secondary_phone:
            user.phone_number2 = secondary_phone
            update_fields.append("phone_number2")

    if update_fields:
        user.save(update_fields=update_fields)
    return user


def get_or_create_student(full_name: str, primary_phone: str | None, group: Group, contract: bool, user: User | None, coin: int):
    if user:
        student = Student.objects.filter(user=user).first()
    elif primary_phone:
        student = Student.objects.filter(phone_number=primary_phone).first()
    else:
        student = Student.objects.filter(
            full_name=full_name,
            center=group.course.center,
            group=group,
        ).first()

    created = False
    if not student:
        student = Student.objects.create(
            user=user,
            full_name=full_name,
            phone_number=primary_phone,
            group=group,
            center=group.course.center,
            contract=contract,
            used_coin=0,
        )
        created = True
    else:
        update_fields = []
        if user and student.user_id != user.id:
            student.user = user
            update_fields.append("user")
        if full_name and student.full_name != full_name:
            student.full_name = full_name
            update_fields.append("full_name")
        if primary_phone and student.phone_number != primary_phone:
            student.phone_number = primary_phone
            update_fields.append("phone_number")
        if student.center_id != group.course.center_id:
            student.center = group.course.center
            update_fields.append("center")
        if student.group_id is None:
            student.group = group
            update_fields.append("group")
        if student.contract != contract:
            student.contract = contract
            update_fields.append("contract")
        if update_fields:
            student.save(update_fields=update_fields)

    student.groups.add(group)
    _sync_import_coin(student, group, coin)
    return student, created


def _sync_import_coin(student: Student, group: Group, coin: int) -> None:
    score = GroupScore.objects.filter(student=student, group=group, reason=IMPORT_SCORE_REASON).first()
    if score:
        changed = False
        if score.score != coin:
            score.score = coin
            changed = True
        if changed:
            score.save(update_fields=["score"])
        return

    GroupScore.objects.create(
        student=student,
        group=group,
        score=coin,
        reason=IMPORT_SCORE_REASON,
    )


def import_students(excel_path: str) -> None:
    sheets = load_student_sheets(excel_path)
    created_count = 0
    updated_count = 0

    with transaction.atomic():
        for sheet in sheets:
            teacher = find_teacher(sheet["sheet_name"], sheet["title"], sheet["index"])
            column_indexes = detect_column_indexes(sheet["headers"])
            print(f"[SHEET] {sheet['sheet_name']} -> teacher_id={teacher.id}")

            for row in sheet["rows"]:
                values = list(row["values"])
                full_name = build_full_name(
                    row_value(values, column_indexes["last_name"]),
                    row_value(values, column_indexes["first_name"]),
                )
                if not full_name:
                    print(f"[SKIPPED] {sheet['sheet_name']} row={row['__excel_row__']} full_name bo'sh")
                    continue

                phone_indexes = column_indexes["phone_indexes"]
                contract_indexes = column_indexes["contract_indexes"]

                primary_phone, secondary_phone = choose_primary_phone(
                    *[row_value(values, phone_index) for phone_index in phone_indexes]
                )
                birthday = normalize_birthday(row_value(values, column_indexes["birthday"]))
                contract = any(
                    normalize_contract(row_value(values, contract_index)) for contract_index in contract_indexes
                )
                arrival_date = normalize_arrival_date(row_value(values, column_indexes["arrival_date"]))
                raw_time = row_value(values, column_indexes["time"])
                if clean_text(raw_time) is None:
                    print(
                        f"[SKIPPED] {sheet['sheet_name']} row={row['__excel_row__']} "
                        f"DARS VAQTI bo'sh"
                    )
                    continue
                try:
                    days_choice, start_lesson = parse_day_and_time(raw_time)
                except ValueError as exc:
                    print(
                        f"[SKIPPED] {sheet['sheet_name']} row={row['__excel_row__']} "
                        f"{exc}"
                    )
                    continue
                coin = normalize_coin(row_value(values, column_indexes["coin"]))

                try:
                    group = select_group(teacher, sheet["sheet_name"], sheet["title"], days_choice, start_lesson)
                except ValueError as exc:
                    print(
                        f"[SKIPPED] {sheet['sheet_name']} row={row['__excel_row__']} "
                        f"{exc}"
                    )
                    continue
                user = upsert_student_user(full_name, primary_phone, secondary_phone, birthday)
                student, created = get_or_create_student(full_name, primary_phone, group, contract, user, coin)

                if arrival_date:
                    aware_dt = make_aware_midday(arrival_date)
                    Student.objects.filter(pk=student.pk).update(created_at=aware_dt)

                if created:
                    created_count += 1
                    print(
                        f"[CREATED] student row={row['__excel_row__']} "
                        f"name={full_name} group={group.title}"
                    )
                else:
                    updated_count += 1
                    print(
                        f"[UPDATED] student row={row['__excel_row__']} "
                        f"name={full_name} group={group.title}"
                    )

    print(f"Student import yakunlandi. created={created_count}, updated={updated_count}")


if __name__ == "__main__":
    args = parse_args("Import students from CRM.xlsx", DEFAULT_STUDENT_EXCEL_PATH)
    excel_path = args.excel_path or DEFAULT_STUDENT_EXCEL_PATH
    import_students(excel_path)
