from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from apps.group.models.grade import Grade
from apps.group.models.group import Group
from apps.group.permissions import (
    IsTeacherOrStudentUser,
    IsTeacherUser,
    get_student_profile,
    get_teacher_profile,
    user_can_access_group_as_student,
)
from apps.group.serializers.grade import GradeModelSerializer

@extend_schema(tags=['Group'])
class GradeCreateAPIView(generics.CreateAPIView):
    serializer_class = GradeModelSerializer
    permission_classes = [IsAuthenticated, IsTeacherUser]

    def get_queryset(self):
        return Grade.objects.select_related("student", "group")


@extend_schema(tags=['Group'])
class GroupGradeAPIView(generics.ListAPIView):
    serializer_class = GradeModelSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrStudentUser]

    def get_queryset(self):
        group_id = self.kwargs.get("id")
        user = self.request.user
        group = get_object_or_404(
            Group.objects.select_related("teacher", "assistant_teacher"),
            pk=group_id,
        )
        qs = Grade.objects.filter(group_id=group_id).select_related("student", "group")

        teacher = get_teacher_profile(user)
        student = get_student_profile(user)

        if teacher:
            if group.teacher_id != teacher.id and group.assistant_teacher_id != teacher.id:
                raise PermissionDenied("Siz bu guruh baholarini ko'ra olmaysiz.")
        elif student:
            if not user_can_access_group_as_student(group, student):
                raise PermissionDenied("Siz bu guruh baholarini ko'ra olmaysiz.")
            qs = qs.filter(student=student)
        else:
            raise PermissionDenied("Siz bu endpointdan foydalana olmaysiz.")

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")

        if month:
            try:
                month = int(month)
            except ValueError:
                return Grade.objects.none()

            if not year:
                year = timezone.now().year
            else:
                try:
                    year = int(year)
                except ValueError:
                    return Grade.objects.none()

            qs = qs.filter(date__year=year, date__month=month)

        return qs.order_by("student__full_name", "date")
