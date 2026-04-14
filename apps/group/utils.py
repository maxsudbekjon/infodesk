from django.utils import timezone

from apps.group.models.group import Group
from apps.pupil.choices import STUDENT_STATUS
from apps.pupil.models.student import Student


def get_group_students_queryset(group_id):
    return (
        Student.objects.filter(groups__id=group_id)
        .exclude(status__in=[STUDENT_STATUS.ARCHIVED, STUDENT_STATUS.FROZEN])
        .distinct()
    )


def get_student_groups_queryset(student):
    return Group.objects.filter(students=student).distinct()


def get_group_students(group):
    return sorted(
        get_group_students_queryset(group.id),
        key=lambda student: ((student.full_name or "").lower(), student.id),
    )


def count_group_students(group):
    return get_group_students_queryset(group.id).count()


def build_student_image_url(student, request=None):
    image = getattr(student, "image", None)
    if not image:
        return None

    if request:
        return request.build_absolute_uri(image.url)

    return image.url


def parse_month_year_query_params(request):
    current_date = timezone.localdate()
    month = request.query_params.get("month")
    year = request.query_params.get("year")

    if month is None:
        month = current_date.month

    if year is None:
        year = current_date.year

    try:
        month = int(month)
        year = int(year)
    except (TypeError, ValueError):
        return None, None

    if month < 1 or month > 12:
        return None, None

    return month, year
