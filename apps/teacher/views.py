from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema

from rest_framework import generics, status
from rest_framework.generics import DestroyAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.teacher.models import Teacher
from apps.teacher.permissions import TeacherImagePermission, IsOrganizationOwner
from apps.teacher.serializers import TeacherSerializer, TeacherListSerializer, TeacherImageUploadSerializer, \
    TeacherCreateSerializer, TeacherUpdateSerializer


@extend_schema(tags=["Teachers"])
class TeacherListAPIView(generics.ListAPIView):
    serializer_class = TeacherListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        branch_id = self.request.query_params.get('branch')
        is_archived = self.request.query_params.get('is_archived')
        search = self.request.query_params.get('search')

        qs = Teacher.objects.select_related('user', 'branch')

        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        if is_archived is not None:
            qs = qs.filter(is_archived=is_archived)

        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__phone_number__icontains=search)
            )

        return qs.order_by('-id')


@extend_schema(tags=["Teachers"])
class TeacherCreateAPIView(generics.CreateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherCreateSerializer
    permission_classes = [IsAuthenticated, IsOrganizationOwner]


@extend_schema(tags=["Teachers"])
class TeacherDetailAPIView(generics.RetrieveAPIView):
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Teacher.objects.select_related(
            'user', 'branch'
        ).prefetch_related(
            'specialty',
            'main_groups__students',
            'teacher_courses__groups'
        ).annotate(
            groups_count=Count('main_groups', distinct=True),
            students_count=Count('main_groups__students', distinct=True),
            courses_count=Count('teacher_courses', distinct=True)
        )


@extend_schema(tags=["Teachers"])
class TeacherToggleArchiveAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizationOwner]

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


@extend_schema(tags=["Teachers"])
class TeacherDeleteAPIView(DestroyAPIView):
    permission_classes = [IsAuthenticated, IsOrganizationOwner]
    queryset = Teacher.objects.all()

    def get_queryset(self):
        return Teacher.objects.filter(
            branch__organization__owner=self.request.user
        )

    def perform_destroy(self, instance):
        instance.delete()


@extend_schema(tags=["Teachers"])
class TeacherUpdateAPIView(UpdateAPIView):
    permission_classes = [IsAuthenticated, TeacherImagePermission]
    serializer_class = TeacherUpdateSerializer

    def get_queryset(self):
        return Teacher.objects.filter(
            branch__organization__owner=self.request.user
        )
