from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.pupil.models.student import Student


def recalculate_student_total_coin(student_id: int) -> int:
    from apps.group.models.score import GroupScore

    student = Student.objects.only("id", "used_coin").get(pk=student_id)
    earned_coin = (
        GroupScore.objects.filter(student_id=student_id)
        .aggregate(total_coin=Coalesce(Sum("score"), 0))
        .get("total_coin", 0)
        or 0
    )
    available_coin = max(int(earned_coin) - int(student.used_coin or 0), 0)
    Student.objects.filter(pk=student_id).update(total_coin=available_coin)
    return available_coin
