from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.template.context_processors import request

from drf_spectacular.utils import extend_schema

from rest_framework import generics, status
from rest_framework.generics import DestroyAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.teacher.models import Teacher
from apps.teacher.permissions import TeacherImagePermission, IsOrganizationOwner
from apps.teacher.serializers import (
    TeacherArchiveToggleResponseSerializer,
    TeacherDeleteResponseSerializer,
    TeacherProfileSerializer,
    TeacherSerializer,
    TeacherListSerializer,
    TeacherImageUploadSerializer,
    TeacherCreateSerializer,
    TeacherUpdateSerializer,
    TeacherGroupSerializer,
)
from apps.group.models import Group
from apps.group.serializers.group import CourseTemplateModelSerializer
from apps.group.models.course import CourseTemplate
from apps.group.permissions import IsTeacherUser
from apps.pupil.models import Student
from apps.user.profile_resolver import get_teacher_profile


def get_teacher_groups_queryset(teacher, course_id=None):
    queryset = Group.objects.select_related(
        "course",
        "room",
    ).filter(Q(teacher=teacher) | Q(assistant_teacher=teacher))

    if course_id is not None:
        queryset = queryset.filter(course_id=course_id)

    return queryset.prefetch_related("lessons_days", "students", "student_set").order_by("-created_at")


def count_distinct_teacher_courses(groups_queryset):
    return groups_queryset.order_by().values_list("course_id", flat=True).distinct().count()


@extend_schema(tags=["Teachers"])
class TeacherListAPIView(generics.ListAPIView):
    serializer_class = TeacherListSerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwner]

    def get_queryset(self):
        branch_id = self.request.query_params.get('branch')
        is_archived = self.request.query_params.get('is_archived')
        search = self.request.query_params.get('search')

        qs = Teacher.objects.select_related('user', 'branch', 'branch__organization').filter(branch__organization__owner=self.request.user)

        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        if is_archived is not None:
            qs = qs.filter(is_archived=is_archived)

        if search:
            qs = qs.filter(
                Q(user__full_name__icontains=search) |
                Q(user__phone_number__icontains=search)
            )

        return qs.order_by('-id')

    # def post(self, request):
    #     branch_id = request.data.get("branch_id")
    #     search = request.data.get("search")
    #     is_archived = request.data.get("is_archived")
    #
    #     qs = Teacher.objects.select_related(
    #         "user",
    #         "branch",
    #         "branch__organization"
    #     ).filter(
    #         branch__organization__owner=request.user
    #     )
    #
    #     if branch_id:
    #         qs = qs.filter(branch_id=branch_id)
    #
    #     if is_archived is not None:
    #         qs = qs.filter(is_archived=is_archived)
    #
    #     if search:
    #         qs = qs.filter(
    #             Q(user__full_name__icontains=search) |
    #             Q(user__phone_number__icontains=search)
    #         )
    #
    #     serializer = TeacherListSerializer(qs, many=True, context={"request": request})
    #     return Response(serializer.data)


@extend_schema(tags=["Teachers"])
class TeacherCreateAPIView(generics.CreateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherCreateSerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwner]


@extend_schema(tags=["Teachers"])
class TeacherDetailAPIView(generics.RetrieveAPIView):
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwner]

    def get_queryset(self):
        return Teacher.objects.select_related(
            'user', 'branch', 'branch__organization'
        ).prefetch_related(
            'specialty',
            'main_groups__students',
            'main_groups__student_set',
            'main_groups__course',
            'main_groups__lessons_days',
            'main_groups__room',
        ).filter(branch__organization__owner=self.request.user).annotate(
            groups_count=Count('main_groups', distinct=True),
            students_count=Count('main_groups__students', distinct=True),
            courses_count=Count('main_groups__course', distinct=True),
        )


@extend_schema(tags=["Teachers"])
class TeacherToggleArchiveAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationOwner]
    serializer_class = TeacherArchiveToggleResponseSerializer

    @extend_schema(responses=TeacherArchiveToggleResponseSerializer)
    def post(self, request, pk):
        teacher = get_object_or_404(
            Teacher.objects.select_related("branch__organization"),
            pk=pk,
            branch__organization__owner=request.user
        )

        teacher.is_archived = not teacher.is_archived
        teacher.save(update_fields=["is_archived"])

        return Response({
            "id": teacher.id,
            "is_archived": teacher.is_archived
        })


@extend_schema(tags=["Teachers"])
class TeacherUploadImageAPIView(generics.GenericAPIView):
    serializer_class = TeacherImageUploadSerializer
    permission_classes = [IsAuthenticated, TeacherImagePermission]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, pk):
        teacher = get_object_or_404(
            Teacher,
            pk=pk,
        )
        self.check_object_permissions(request, teacher)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        teacher.image = serializer.validated_data["image"]
        teacher.save(update_fields=["image"])

        return Response({
            "image_url": request.build_absolute_uri(
                teacher.image.url
            )
        })


@extend_schema(tags=["Teachers"], responses={204: None})
class TeacherDeleteAPIView(DestroyAPIView):
    permission_classes = [IsAuthenticated, IsOrganizationOwner]
    serializer_class = TeacherDeleteResponseSerializer
    queryset = Teacher.objects.all()
    http_method_names = ["delete", "head", "options"]

    def get_queryset(self):
        return Teacher.objects.filter(
            branch__organization__owner=self.request.user
        )

    def perform_destroy(self, instance):
        instance.delete()


@extend_schema(tags=["Teachers"])
class TeacherUpdateAPIView(UpdateAPIView):
    permission_classes = [IsAuthenticated, TeacherImagePermission, IsOrganizationOwner]
    serializer_class = TeacherUpdateSerializer

    def get_queryset(self):
        return Teacher.objects.filter(
            branch__organization__owner=self.request.user
        )


@extend_schema(
    tags=["Teachers"],
    summary="List of groups for the logged-in teacher",
    description=(
        "Returns groups where the current user is assigned as teacher or assistant teacher. "
        "Accessible only for teacher accounts."
    ),
)
class TeacherGroupListAPIView(generics.ListAPIView):
    serializer_class = TeacherGroupSerializer
    permission_classes = [IsAuthenticated, IsTeacherUser]

    def get_queryset(self):
        teacher = get_teacher_profile(self.request.user)
        if not teacher:
            return Group.objects.none()

        return get_teacher_groups_queryset(teacher)


@extend_schema(
    tags=["Teachers"],
    summary="List of courses for the logged-in teacher",
    description="Returns distinct courses where the current teacher is assigned to at least one group "
                "as main or assistant teacher.",
)
class TeacherCourseListAPIView(generics.ListAPIView):
    serializer_class = CourseTemplateModelSerializer
    permission_classes = [IsAuthenticated, IsTeacherUser]

    def get_queryset(self):
        teacher = get_teacher_profile(self.request.user)
        if not teacher:
            return CourseTemplate.objects.none()

        course_ids = (
            Group.objects.filter(Q(teacher=teacher) | Q(assistant_teacher=teacher))
            .values_list("course_id", flat=True)
        )
        return CourseTemplate.objects.filter(id__in=course_ids).distinct().order_by("-created_at")


@extend_schema(
    tags=["Teachers"],
    summary="Groups for the logged-in teacher",
    description=(
        "Returns groups where the current teacher is assigned as main or assistant. "
        "If course_id is provided in the URL, the result is limited to that course."
    ),
)
class TeacherCourseGroupsAPIView(generics.ListAPIView):
    serializer_class = TeacherGroupSerializer
    permission_classes = [IsAuthenticated, IsTeacherUser]

    def get_queryset(self):
        teacher = get_teacher_profile(self.request.user)
        if not teacher:
            return Group.objects.none()

        course_id = self.kwargs.get("course_id")
        return get_teacher_groups_queryset(teacher, course_id=course_id)


@extend_schema(
    tags=["Teachers"],
    summary="Current teacher profile",
    description="Returns detailed profile of the logged-in teacher.",
)
class TeacherMeAPIView(generics.RetrieveAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated, IsTeacherUser]

    def get_object(self):
        teacher = get_object_or_404(
            Teacher.objects.select_related(
                'user',
                'branch',
                'branch__organization',
            ).prefetch_related(
                'specialty',
            ),
            user=self.request.user,
        )

        groups_qs = get_teacher_groups_queryset(teacher)
        teacher.profile_groups = list(groups_qs)
        teacher.groups_count = groups_qs.count()
        teacher.courses_count = count_distinct_teacher_courses(groups_qs)
        teacher.students_count = (
            Student.objects.filter(
                Q(group__in=groups_qs) | Q(groups__in=groups_qs)
            )
            .distinct()
            .count()
        )
        return teacher
