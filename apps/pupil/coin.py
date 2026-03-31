from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.pupil.models.student import Student

IMPORT_SCORE_REASON = "CRM-2.xlsx import coin"


def get_student_earned_coin(student_id: int, *, include_import: bool = False) -> int:
    from apps.group.models.score import GroupScore

    queryset = GroupScore.objects.filter(student_id=student_id)
    if not include_import:
        queryset = queryset.exclude(reason=IMPORT_SCORE_REASON)

    earned_coin = (
        queryset.aggregate(total_coin=Coalesce(Sum("score"), 0)).get("total_coin", 0) or 0
    )
    return int(earned_coin)


def calculate_student_coin_offset(student_id: int, target_balance: int) -> int:
    student = Student.objects.only("id", "used_coin").get(pk=student_id)
    earned_coin = get_student_earned_coin(student_id)
    return int(target_balance or 0) + int(student.used_coin or 0) - earned_coin


def recalculate_student_total_coin(student_id: int) -> int:
    student = Student.objects.only("id", "used_coin", "coin_offset").get(pk=student_id)
    earned_coin = get_student_earned_coin(student_id)
    available_coin = max(
        int(student.coin_offset or 0) + int(earned_coin) - int(student.used_coin or 0),
        0,
    )
    Student.objects.filter(pk=student_id).update(total_coin=available_coin)
    return available_coin
