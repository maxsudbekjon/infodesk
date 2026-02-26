# from django.shortcuts import render
# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.parsers import MultiPartParser, FormParser
# from rest_framework.response import Response
# from django.db.models import Count
# from rest_framework.permissions import IsAuthenticated
# from .models import Teacher
# from .serializers import TeacherSerializer
#
#
# class IsStaffOrReadOnly(IsAuthenticated):
#     # simple: require auth and staff for unsafe methods
#     def has_permission(self, request, view):
#         if request.method in ('GET', 'HEAD', 'OPTIONS'):
#             return super().has_permission(request, view)
#         return super().has_permission(request, view) and request.user.is_staff
#
#
# class TeacherViewSet(viewsets.ModelViewSet):
#     queryset = Teacher.objects.all().select_related('user', 'branch').prefetch_related('specialty')
#     serializer_class = TeacherSerializer
#     permission_classes = [IsStaffOrReadOnly]
#     parser_classes = (MultiPartParser, FormParser)
#     filterset_fields = ('is_archived', 'branch', 'specialty')
#     search_fields = ('user__first_name', 'user__last_name', 'user__phone_number')
#     ordering_fields = ('created_at', 'monthly_salary', 'percentage_share')
#
#     def get_queryset(self):
#         qs = super().get_queryset()
#         # annotate counts if you have related models: groups, students, courses
#         return qs.annotate(
#             groups_count=Count('groups', distinct=True),
#             students_count=Count('groups__students', distinct=True),
#             courses_count=Count('courses', distinct=True)
#         )
#
#     @action(detail=True, methods=['post'], url_path='toggle-archive')
#     def toggle_archive(self, request, pk=None):
#         teacher = self.get_object()
#         teacher.is_archived = not teacher.is_archived
#         teacher.save()
#         return Response({'is_archived': teacher.is_archived})
#
#     @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='upload-image')
#     def upload_image(self, request, pk=None):
#         teacher = self.get_object()
#         file_obj = request.data.get('image')
#         if not file_obj:
#             return Response({'detail': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
#         teacher.image = file_obj
#         teacher.save()
#         return Response({'image_url': request.build_absolute_uri(teacher.image.url)})
#
#     # optional: quick stats endpoint
#     @action(detail=True, methods=['get'], url_path='stats')
#     def stats(self, request, pk=None):
#         t = self.get_object()
#         data = {
#             'courses_count': getattr(t, 'courses_count', 0),
#             'groups_count': getattr(t, 'groups_count', 0),
#             'students_count': getattr(t, 'students_count', 0),
#         }
#         return Response(data)

from django.db.models import Count


from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Teacher
from .serializers import TeacherSerializer

class TeacherListCreateAPIView(generics.ListCreateAPIView):
    queryset = Teacher.objects.all().select_related('user', 'branch').prefetch_related('specialty')
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        # filterlar
        is_archived = self.request.query_params.get('is_archived')
        branch = self.request.query_params.get('branch')
        specialty = self.request.query_params.get('specialty')
        search = self.request.query_params.get('search')

        if is_archived is not None:
            qs = qs.filter(is_archived=is_archived)

        if branch:
            qs = qs.filter(branch_id=branch)

        if specialty:
            qs = qs.filter(specialty__id=specialty)

        if search:
            qs = qs.filter(
                user__first_name__icontains=search
            ) | qs.filter(
                user__last_name__icontains=search
            ) | qs.filter(
                user__phone_number__icontains=search
            )

        return qs.annotate(
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
            teacher = Teacher.objects.get(pk=pk)
        except Teacher.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)

        teacher.is_archived = not teacher.is_archived
        teacher.save()

        return Response({
            'id': teacher.id,
            'is_archived': teacher.is_archived
        })


class TeacherUploadImageAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, pk):
        try:
            teacher = Teacher.objects.get(pk=pk)
        except Teacher.DoesNotExist:
            return Response({'detail': 'Not found'}, status=404)

        image = request.data.get('image')
        if not image:
            return Response({'detail': 'Image not provided'}, status=400)

        teacher.image = image
        teacher.save()

        return Response({
            'image_url': request.build_absolute_uri(teacher.image.url)
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

