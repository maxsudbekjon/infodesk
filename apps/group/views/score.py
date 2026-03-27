from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

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
from apps.group.serializers.score import GroupScoreCreateSerializer, GroupScoreUpdateSerializer

@extend_schema(tags=['Group'])
class GroupScoreCreateAPIView(generics.CreateAPIView):
    queryset = GroupScore.objects.all()
    serializer_class = GroupScoreCreateSerializer
    permission_classes = [IsAuthenticated, IsTeacherUser]


@extend_schema(tags=['Group'])
class GroupScoreUpdateAPIView(generics.UpdateAPIView):
    serializer_class = GroupScoreUpdateSerializer
    permission_classes = [IsAuthenticated, IsTeacherUser]
    lookup_field = "id"

    def get_queryset(self):
        teacher = get_teacher_profile(self.request.user)
        if not teacher:
            return GroupScore.objects.none()

        queryset = GroupScore.objects.select_related("group", "student")
        return filter_group_queryset_for_teacher(queryset, teacher)


@extend_schema(tags=['Group'])
class GroupScoreListAPIView(generics.ListAPIView):
    serializer_class = GroupScoreCreateSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrStudentUser]

    def get_queryset(self):
        group_id = self.kwargs["id"]
        user = self.request.user
        group = get_object_or_404(
            Group.objects.select_related("teacher", "assistant_teacher"),
            pk=group_id,
        )
        qs = GroupScore.objects.filter(group_id=group_id).select_related("group", "student")

        teacher = get_teacher_profile(user)
        student = get_student_profile(user)

        if teacher:
            if group.teacher_id != teacher.id and group.assistant_teacher_id != teacher.id:
                raise PermissionDenied("Siz bu guruh coinlarini ko'ra olmaysiz.")
        elif student:
            if not user_can_access_group_as_student(group, student):
                raise PermissionDenied("Siz bu guruh coinlarini ko'ra olmaysiz.")
            qs = qs.filter(student=student)
        else:
            raise PermissionDenied("Siz bu endpointdan foydalana olmaysiz.")

        return qs.order_by("-created_at", "student__full_name")
