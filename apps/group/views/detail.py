from django.db import models
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from apps.group.models import Group
from apps.group.serializers import GroupDetailModelSerializer
from apps.group.serializers.detail import GroupStudentModelSerializer
from apps.group.permissions import IsTeacherUser
from apps.user.profile_resolver import get_teacher_profile


@extend_schema(tags=['Group'])
class GroupDetailAPIView(generics.RetrieveAPIView):
    serializer_class = GroupDetailModelSerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        organizations = user.organization.all()
        if not organizations.exists():
            return Group.objects.none()
        return Group.objects.select_related("room", "course", "branch").filter(
            branch__organization__in=organizations
        )


@extend_schema(
    tags=['Group'],
    summary="Students of a teacher's group",
    description="Returns students belonging to the specified group where the current teacher is assigned "
                "as main or assistant teacher."
)
class GroupStudentAPIView(generics.RetrieveAPIView):
    serializer_class = GroupStudentModelSerializer
    lookup_field = 'id'
    permission_classes = [IsAuthenticated, IsTeacherUser]

    def get_queryset(self):
        teacher = get_teacher_profile(self.request.user)
        if not teacher:
            return Group.objects.none()

        return Group.objects.filter(
            models.Q(teacher=teacher) | models.Q(assistant_teacher=teacher)
        ).prefetch_related("students", "student_set")
