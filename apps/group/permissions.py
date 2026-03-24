from django.db.models import Q
from rest_framework.permissions import BasePermission

from apps.user.profile_resolver import get_student_profile, get_teacher_profile


def filter_group_queryset_for_teacher(queryset, teacher, group_prefix="group"):
    return queryset.filter(
        Q(**{f"{group_prefix}__teacher": teacher})
        | Q(**{f"{group_prefix}__assistant_teacher": teacher})
    )


def user_can_access_group_as_student(group, student):
    return bool(student and group.students.filter(pk=student.pk).exists())


class IsTeacherUser(BasePermission):
    message = "Bu amal faqat teacher account uchun ruxsat etilgan."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and get_teacher_profile(request.user))


class IsTeacherOrStudentUser(BasePermission):
    message = "Bu endpoint faqat teacher yoki student account uchun ruxsat etilgan."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return bool(get_teacher_profile(user) or get_student_profile(user))
