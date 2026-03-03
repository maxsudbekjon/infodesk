from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from apps.group.serializers import GroupDetailModelSerializer, GroupModelSerializer, GroupStatusModelSerializer
from rest_framework.response import Response
from rest_framework import status
from apps.group.models import Group
from drf_spectacular.utils import extend_schema, OpenApiParameter,OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework.pagination import PageNumberPagination



class GroupPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

@extend_schema(tags=['Group'],
               parameters=[
                   OpenApiParameter(
                   name='branch_id',
                   type=OpenApiTypes.INT,
                   location=OpenApiParameter.QUERY,
                   required=True,
                   description='Branch ID for filtering leads'
               ),
               OpenApiParameter(
                   name='status',
                   type=OpenApiTypes.STR,
                   location=OpenApiParameter.QUERY,
                   required=False,
                   enum=['active', 'archived', 'test_lesson', 'frozen']
               ),
               OpenApiParameter(
                   name='teacher_id',
                   type=OpenApiTypes.INT,
                   location=OpenApiParameter.QUERY,
                   required=False,
               ),
               OpenApiParameter(
                   name='course_id',
                   type=OpenApiTypes.INT,
                   location=OpenApiParameter.QUERY,
                   required=False,
               ),
               OpenApiParameter(
                   name='lesson_days',
                   type=OpenApiTypes.STR,
                   location=OpenApiParameter.QUERY,
                   required=False,
                   enum=['odd_days','even_days','every_day']
               ),
               
               ])
class GroupListAPIView(generics.ListAPIView):
    serializer_class = GroupModelSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = GroupPagination

    def get_queryset(self):
        user = self.request.user

        org_ids = list(user.organization_set.values_list('id', flat=True))

        if not org_ids:
            return Group.objects.none()

        branch_id = self.request.query_params.get('branch_id')
        if not branch_id:
            return Group.objects.none()

        filters = {
            "branch__organization_id__in": org_ids,
            "branch_id": branch_id
        }

        status = self.request.query_params.get('status')
        teacher_id = self.request.query_params.get('teacher_id')
        course_id = self.request.query_params.get('course_id')
        lesson_days = self.request.query_params.get('lesson_days')

        if status:
            filters["status"] = status
        if teacher_id:
            filters["teacher_id"] = teacher_id
        if course_id:
            filters["course_id"] = course_id
        if lesson_days:
            filters["lessons_days_choice"] = lesson_days

        return (
            Group.objects
            .select_related("course", "teacher", "room", "branch")
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
    
@extend_schema(tags=['Group'])
class GroupStatusUpdateAPIView(generics.UpdateAPIView):
    serializer_class = GroupStatusModelSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Group.objects.all()

    def perform_update(self, serializer):
        serializer.save()


@extend_schema(tags=['Group'])
class GroupCreateAPIView(generics.CreateAPIView):
    queryset=Group.objects.all()
    serializer_class=GroupModelSerializer
    permission_classes=[IsAuthenticated]

@extend_schema(tags=['Group'])
class GroupDetailAPIView(generics.RetrieveAPIView):
    serializer_class=GroupDetailModelSerializer
    lookup_field='id'

    def get_queryset(self):
        user = self.request.user
        organizations = user.organization_set.all()
        if not organizations.exists():
            return Group.objects.none()
        return Group.objects.select_related('room', 'course', 'branch').filter(
            branch__organization__in=organizations
        )
