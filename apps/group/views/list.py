from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from apps.group.models import Group
from apps.group.serializers import GroupModelSerializer
from apps.group.views.pagination import GroupPagination


@extend_schema(
    tags=["Group"],
    parameters=[
        OpenApiParameter(
            name="branch_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Branch ID for filtering leads",
        ),
        OpenApiParameter(
            name="status",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            enum=["active", "archived", "test_lesson", "frozen"],
        ),
        OpenApiParameter(
            name="teacher_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
        OpenApiParameter(
            name="course_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
        OpenApiParameter(
            name="lesson_days",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            enum=["odd_days", "even_days", "every_day"],
        ),
    ],
)
class GroupListAPIView(generics.ListAPIView):
    serializer_class = GroupModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = GroupPagination

    def get_queryset(self):
        user = self.request.user
        org_ids = list(user.organization_set.values_list("id", flat=True))
        if not org_ids:
            return Group.objects.none()

        branch_id = self.request.query_params.get("branch_id")

        filters = {
            "branch__organization_id__in": org_ids,
            "branch_id": branch_id,
        }

        status = self.request.query_params.get("status")
        teacher_id = self.request.query_params.get("teacher_id")
        course_id = self.request.query_params.get("course_id")
        lesson_days = self.request.query_params.get("lesson_days")

        if status:
            filters["status"] = status
        if teacher_id:
            filters["teacher_id"] = teacher_id
        if course_id:
            filters["course_id"] = course_id
        if lesson_days:
            filters["lessons_days_choice"] = lesson_days

        return (
            Group.objects.select_related("course", "teacher", "room", "branch")
            .filter(**filters)
            .only(
                "id",
                "title",
                "status",
                "lessons_days_choice",
                "start_lesson",
                "end_lesson",
                "total_student",
                "started_at",
                "closed_at",
                "course_id",
                "teacher_id",
                "room_id",
                "branch_id",
            )
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
