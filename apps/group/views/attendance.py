import calendar
from collections import defaultdict
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied, ValidationError as DRFValidationError
from rest_framework.response import Response
from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.group.models.attendance import Attendance
from apps.group.models.group import Group
from apps.group.models.score import GroupScore
from apps.group.permissions import (
    IsTeacherOrStudentUser,
    IsTeacherUser,
    filter_group_queryset_for_teacher,
    get_student_profile,
    get_teacher_profile,
    user_can_access_group_as_student,
)
from apps.group.serializers.attendance import (
    AttendanceModelSerializer,
    AttendanceUpdateSerializer,
    GroupAttendanceModelSerializer,
)
from apps.group.serializers.monthly_attendance import GroupMonthlyAttendanceResponseSerializer
from apps.group.utils import build_student_image_url, get_group_students, parse_month_year_query_params

class AttendancePagination(PageNumberPagination):
    page_size = 20


def _get_accessible_group_for_user(request, group_id):
    group = get_object_or_404(
        Group.objects.select_related("teacher", "assistant_teacher"),
        pk=group_id,
    )

    teacher = get_teacher_profile(request.user)
    student = get_student_profile(request.user)

    if teacher:
        if group.teacher_id != teacher.id and group.assistant_teacher_id != teacher.id:
            raise PermissionDenied("Siz bu guruh davomatini ko'ra olmaysiz.")
    elif student:
        if not user_can_access_group_as_student(group, student):
            raise PermissionDenied("Siz bu guruh davomatini ko'ra olmaysiz.")
    else:
        raise PermissionDenied("Siz bu endpointdan foydalana olmaysiz.")

    return group, teacher, student


@extend_schema(tags=['Group'])
class AttendanceCreateAPIView(generics.CreateAPIView):
    serializer_class = AttendanceModelSerializer
    permission_classes = [IsAuthenticated, IsTeacherUser]

    def get_queryset(self):
        return Attendance.objects.select_related('group', 'student')

    def perform_create(self, serializer):
        student = serializer.validated_data.get('student')
        group = serializer.validated_data.get('group')

        if not user_can_access_group_as_student(group, student):
            raise ValidationError({'detail': 'This student not found in this group'})

        serializer.save()


@extend_schema(tags=['Group'])
class AttendanceUpdateAPIView(generics.UpdateAPIView):
    serializer_class = AttendanceUpdateSerializer
    permission_classes = [IsAuthenticated, IsTeacherUser]
    lookup_field = "id"

    def get_queryset(self):
        teacher = get_teacher_profile(self.request.user)
        if not teacher:
            return Attendance.objects.none()

        queryset = Attendance.objects.select_related("group", "student")
        return filter_group_queryset_for_teacher(queryset, teacher)


@extend_schema(tags=['Group'])
class GroupAttendanceAPIView(generics.ListAPIView):
    serializer_class = GroupAttendanceModelSerializer
    pagination_class = AttendancePagination
    permission_classes = [IsAuthenticated, IsTeacherOrStudentUser]

    def get_queryset(self):
        group_id = self.kwargs["id"]
        _group, _teacher, student = _get_accessible_group_for_user(self.request, group_id)

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")

        qs = Attendance.objects.filter(group_id=group_id)

        if student:
            qs = qs.filter(student=student)

        if month and year:
            qs = qs.filter(date__year=year, date__month=month)

        return qs.select_related("student", "group").order_by("date")


@extend_schema(
    tags=['Group'],
    parameters=[
        OpenApiParameter(
            name="month",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Month number from 1 to 12. Defaults to the current month.",
        ),
        OpenApiParameter(
            name="year",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Year. Defaults to the current year.",
        ),
    ],
)
class GroupMonthlyAttendanceAPIView(generics.ListAPIView):
    serializer_class = GroupMonthlyAttendanceResponseSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, IsTeacherOrStudentUser]

    def list(self, request, *args, **kwargs):
        group_id = self.kwargs["id"]
        group, _teacher, student = _get_accessible_group_for_user(request, group_id)

        month, year = parse_month_year_query_params(request)
        if month is None or year is None:
            raise DRFValidationError({"month": "Invalid month or year."})

        days = list(range(1, calendar.monthrange(year, month)[1] + 1))

        students = get_group_students(group)
        if student:
            students = [item for item in students if item.id == student.id]

        attendance_map = defaultdict(dict)
        attendance_qs = Attendance.objects.filter(
            group_id=group_id,
            date__year=year,
            date__month=month,
        )
        for attendance in attendance_qs.only("id", "student_id", "date", "is_present"):
            attendance_map[attendance.student_id][attendance.date.day] = {
                "id": attendance.id,
                "is_present": attendance.is_present,
            }

        coin_map = {
            row["student_id"]: row["total_coin"]
            for row in (
                GroupScore.objects.filter(
                    group_id=group_id,
                    created_at__year=year,
                    created_at__month=month,
                )
                .values("student_id")
                .annotate(total_coin=Coalesce(Sum("score"), 0))
            )
        }

        payload = {
            "month": month,
            "year": year,
            "days": days,
            "students": [
                {
                    "id": item.id,
                    "full_name": item.full_name,
                    "image": build_student_image_url(item, request=request),
                    "coin": coin_map.get(item.id, 0),
                    "attendance_days": [
                        {
                            "id": attendance_map.get(item.id, {}).get(day, {}).get("id"),
                            "day": day,
                            "is_present": attendance_map.get(item.id, {}).get(day, {}).get("is_present"),
                        }
                        for day in days
                    ],
                }
                for item in students
            ],
        }

        serializer = self.get_serializer(payload)
        return Response(serializer.data)
