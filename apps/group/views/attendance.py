from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics
from apps.group.models.attendance import Attendance
from apps.group.models.group import Group
from apps.group.serializers.attendance import AttendanceModelSerializer, GroupAttendanceModelSerializer
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied

from apps.group.permissions import (
    IsTeacherOrStudentUser,
    IsTeacherUser,
    get_student_profile,
    get_teacher_profile,
)

class AttendancePagination(PageNumberPagination):
    page_size = 20

@extend_schema(tags=['Group'])
class AttendanceCreateAPIView(generics.CreateAPIView):
    serializer_class = AttendanceModelSerializer
    permission_classes = [IsAuthenticated, IsTeacherUser]

    def get_queryset(self):
        return Attendance.objects.select_related('group', 'student')

    def perform_create(self, serializer):
        student = serializer.validated_data.get('student')
        group = serializer.validated_data.get('group')

        if not group.students.filter(id=student.id).exists():
            raise ValidationError({'detail': 'This student not found in this group'})

        serializer.save()
        
@extend_schema(tags=['Group'])
class GroupAttendanceAPIView(generics.ListAPIView):
    serializer_class = GroupAttendanceModelSerializer
    pagination_class = AttendancePagination
    permission_classes = [IsAuthenticated, IsTeacherOrStudentUser]

    def get_queryset(self):
        group_id = self.kwargs["id"]
        user = self.request.user
        group = get_object_or_404(
            Group.objects.select_related("teacher", "assistant_teacher"),
            pk=group_id,
        )

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")

        qs = Attendance.objects.filter(group_id=group_id)

        teacher = get_teacher_profile(user)
        student = get_student_profile(user)

        if teacher:
            if group.teacher_id != teacher.id and group.assistant_teacher_id != teacher.id:
                raise PermissionDenied("Siz bu guruh davomatini ko'ra olmaysiz.")
        elif student:
            if not group.students.filter(pk=student.pk).exists():
                raise PermissionDenied("Siz bu guruh davomatini ko'ra olmaysiz.")
            qs = qs.filter(student=student)
        else:
            raise PermissionDenied("Siz bu endpointdan foydalana olmaysiz.")

        if month and year:
            qs = qs.filter(date__year=year, date__month=month)

        return qs.select_related("student", "group").order_by("date")
