from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError, ProgrammingError

from apps.pupil.models import Student
from apps.user.choices import ROLE


SAFE_STUDENT_ONLY_FIELDS = (
    "id",
    "full_name",
    "image",
    "phone_number",
    "group_id",
    "center_id",
    "status",
    "created_at",
    "updated_at",
)


def get_teacher_profile(user):
    return getattr(user, "teachers", None)


def get_student_profile(user):
    if not user or not getattr(user, "is_authenticated", False):
        return None

    try:
        student = getattr(user, "student_profile")
        if student:
            return student
    except (ObjectDoesNotExist, OperationalError, ProgrammingError):
        pass

    if getattr(user, "role", None) != ROLE.STUDENT:
        return None

    return find_student_by_phone_number(user.phone_number)


def find_student_by_phone_number(phone_number):
    if not phone_number:
        return None

    return (
        Student.objects.only(*SAFE_STUDENT_ONLY_FIELDS)
        .filter(phone_number=phone_number)
        .first()
    )
