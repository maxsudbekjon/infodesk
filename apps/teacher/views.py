from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from apps.teacher.models import Teacher
from apps.teacher.serializers import TeacherSerializer, TeacherListSerializer, TeacherImageUploadSerializer


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


class TeacherCreateAPIView(generics.CreateAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]


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


class TeacherRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Teacher.objects.all().select_related('user', 'branch').prefetch_related('specialty')
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().annotate(
            groups_count=Count('main_groups', distinct=True),
            students_count=Count('main_groups__students', distinct=True),
            courses_count=Count('teacher_courses', distinct=True)
        )


class TeacherToggleArchiveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            teacher = Teacher.objects.get(pk=pk, center_id=request.user.center_id)
        except Teacher.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)

        teacher.is_archived = not teacher.is_archived
        teacher.save()

        return Response({
            'id': teacher.id,
            'is_archived': teacher.is_archived
        })


# class TeacherUploadImageAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = (MultiPartParser, FormParser)
#
#     def post(self, request, pk):
#         try:
#             teacher = Teacher.objects.get(pk=pk)
#         except Teacher.DoesNotExist:
#             return Response({'detail': 'Not found'}, status=404)
#
#         image = request.data.get('image')
#         if not image:
#             return Response({'detail': 'Image not provided'}, status=400)
#
#         teacher.image = image
#         teacher.save()
#
#         return Response({
#             'image_url': request.build_absolute_uri(teacher.image.url)
#         })



class TeacherUploadImageAPIView(generics.GenericAPIView):
    serializer_class = TeacherImageUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, pk):
        teacher = get_object_or_404(
            Teacher,
            pk=pk,
            center=request.user.center
        )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        teacher.image = serializer.validated_data["image"]
        teacher.save()

        return Response({
            "image_url": request.build_absolute_uri(teacher.image.url)
        })

class TeacherStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            teacher = Teacher.objects.annotate(
                groups_count=Count('main_groups', distinct=True),
                students_count=Count('main_groups__students', distinct=True),
                courses_count=Count('teacher_courses', distinct=True)
            ).get(pk=pk)
        except Teacher.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)

        return Response({
            'courses_count': teacher.courses_count,
            'groups_count': teacher.groups_count,
            'students_count': teacher.students_count
        })
