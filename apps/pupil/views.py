import calendar
from collections import defaultdict

from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.group.models.attendance import Attendance
from apps.group.models.group import Group
from apps.group.models.score import GroupScore
from apps.group.permissions import user_can_access_group_as_student
from apps.group.serializers.monthly_attendance import GroupMonthlyAttendanceResponseSerializer
from apps.group.utils import (
    build_student_image_url,
    count_group_students,
    parse_month_year_query_params,
)
from apps.group.utils import get_student_groups_queryset
from apps.pupil.models.student import Student
from apps.pupil.models.note import StudentNote
from apps.pupil.serializers.dashboard import (
    StudentCourseSummaryResponseSerializer,
    StudentGroupListResponseSerializer,
)
from apps.pupil.serializers.student import (
    StudentNoteCreateSerializer,
    StudentReturnToLeadSerializer,
)
from apps.user.profile_resolver import get_student_profile


def _get_student_or_403(user):
    student = get_student_profile(user)
    if not student:
        raise PermissionDenied("Bu endpoint faqat student account uchun.")
    return student


class StudentReturnToLeadAPIView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentReturnToLeadSerializer


class StudentNoteCreateAPIView(generics.CreateAPIView):
    queryset = StudentNote.objects.all()
    serializer_class = StudentNoteCreateSerializer


@extend_schema(
    tags=["Student"],
    summary="List groups for the logged-in student",
    description="Returns all groups where the current student is enrolled through either the direct group field or the many-to-many relation.",
)
class StudentGroupListAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentGroupListResponseSerializer

    def get(self, request, *args, **kwargs):
        student = _get_student_or_403(request.user)
        groups = (
            get_student_groups_queryset(student)
            .select_related("course", "branch", "room", "teacher__user", "assistant_teacher__user")
            .prefetch_related("lessons_days", "students", "student_set")
            .order_by("-created_at")
        )

        payload = {
            "groups": [
                {
                    "id": group.id,
                    "title": group.title,
                    "course_id": group.course_id,
                    "course_name": group.course.name if group.course_id else None,
                    "duration_months": group.course.duration_months if group.course_id else None,
                    "branch_id": group.branch_id,
                    "branch_name": group.branch.name if group.branch_id else None,
                    "teacher_id": group.teacher_id,
                    "teacher_name": group.teacher.user.full_name if group.teacher_id and group.teacher and group.teacher.user else None,
                    "assistant_teacher_id": group.assistant_teacher_id,
                    "assistant_teacher_name": (
                        group.assistant_teacher.user.full_name
                        if group.assistant_teacher_id and group.assistant_teacher and group.assistant_teacher.user
                        else None
                    ),
                    "room": group.room.name if group.room_id else None,
                    "lessons_days": [
                        day.day for day in sorted(group.lessons_days.all(), key=lambda item: item.id or 0)
                    ],
                    "lessons_days_choice": group.lessons_days_choice,
                    "status": group.status,
                    "start_lesson": group.start_lesson,
                    "end_lesson": group.end_lesson,
                    "total_student": count_group_students(group),
                    "started_at": group.started_at,
                    "closed_at": group.closed_at,
                }
                for group in groups
            ]
        }

        serializer = self.get_serializer(payload)
        return Response(serializer.data)


@extend_schema(
    tags=["Student"],
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
class StudentMonthlyAttendanceAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupMonthlyAttendanceResponseSerializer

    def get(self, request, group_id, *args, **kwargs):
        student = _get_student_or_403(request.user)
        group = get_object_or_404(Group.objects.select_related("course"), pk=group_id)

        if not user_can_access_group_as_student(group, student):
            raise PermissionDenied("Bu guruh sizga tegishli emas.")

        month, year = parse_month_year_query_params(request)
        if month is None or year is None:
            raise DRFValidationError({"month": "Invalid month or year."})

        days = list(range(1, calendar.monthrange(year, month)[1] + 1))
        attendance_map = defaultdict(dict)

        attendance_qs = Attendance.objects.filter(
            group_id=group.id,
            student=student,
            date__year=year,
            date__month=month,
        )
        for attendance in attendance_qs.only("id", "date", "is_present"):
            attendance_map[student.id][attendance.date.day] = {
                "id": attendance.id,
                "is_present": attendance.is_present,
            }

        coin_row = (
            GroupScore.objects.filter(
                group_id=group.id,
                student=student,
                created_at__year=year,
                created_at__month=month,
            )
            .aggregate(total_coin=Coalesce(Sum("score"), 0))
        )

        payload = {
            "month": month,
            "year": year,
            "days": days,
            "students": [
                {
                    "id": student.id,
                    "full_name": student.full_name,
                    "image": build_student_image_url(student, request=request),
                    "coin": coin_row["total_coin"],
                    "attendance_days": [
                        {
                            "id": attendance_map.get(student.id, {}).get(day, {}).get("id"),
                            "day": day,
                            "is_present": attendance_map.get(student.id, {}).get(day, {}).get("is_present"),
                        }
                        for day in days
                    ],
                }
            ],
        }

        serializer = self.get_serializer(payload)
        return Response(serializer.data)


@extend_schema(tags=["Student"])
class StudentCourseSummaryAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentCourseSummaryResponseSerializer

    def get(self, request, *args, **kwargs):
        student = _get_student_or_403(request.user)

        courses = {}
        student_groups = get_student_groups_queryset(student).select_related("course")
        for group in student_groups:
            course = group.course
            courses[course.id] = {
                "course_id": course.id,
                "course_name": course.name,
                "present_count": 0,
                "absent_count": 0,
                "coin": 0,
            }

        allowed_course_ids = set(courses.keys())

        attendance_rows = Attendance.objects.filter(student=student).select_related("group__course")
        for attendance in attendance_rows:
            if not attendance.group_id or not attendance.group.course_id:
                continue
            if attendance.group.course_id not in allowed_course_ids:
                continue

            item = courses.setdefault(
                attendance.group.course_id,
                {
                    "course_id": attendance.group.course_id,
                    "course_name": attendance.group.course.name,
                    "present_count": 0,
                    "absent_count": 0,
                    "coin": 0,
                },
            )

            if attendance.is_present:
                item["present_count"] += 1
            else:
                item["absent_count"] += 1

        score_rows = GroupScore.objects.filter(student=student).select_related("group__course")
        for score in score_rows:
            if not score.group_id or not score.group.course_id:
                continue
            if score.group.course_id not in allowed_course_ids:
                continue

            item = courses.setdefault(
                score.group.course_id,
                {
                    "course_id": score.group.course_id,
                    "course_name": score.group.course.name,
                    "present_count": 0,
                    "absent_count": 0,
                    "coin": 0,
                },
            )
            item["coin"] += score.score

        payload = {
            "courses": sorted(
                courses.values(),
                key=lambda item: ((item["course_name"] or "").lower(), item["course_id"]),
            )
        }
        serializer = self.get_serializer(payload)
        return Response(serializer.data)
