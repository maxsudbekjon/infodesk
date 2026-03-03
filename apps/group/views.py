from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from apps.group.serializers import GroupDetailModelSerializer, GroupModelSerializer, GroupStatusModelSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from apps.group.models import Group
from apps.settings.models import Branch
from drf_spectacular.utils import extend_schema, OpenApiParameter,OpenApiExample
from drf_spectacular.types import OpenApiTypes





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
    serializer_class=GroupModelSerializer
    permission_classes=[IsAuthenticated]
    def get_queryset(self):
        branch_id=self.request.query_params.get('branch_id')
        if not branch_id:
            return Response(
                {'detail':'Branc_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset=Group.objects.select_related('course','teacher',
                                            'room').filter(course__branch=branch_id)
        status=self.request.query_params.get('status')
        teacher_id=self.request.query_params.get('teacher_id')
        course_id=self.request.query_params.get('course_id')
        lesson_days=self.request.query_params.get('lesson_days')
        if status:
            queryset=queryset.filter(status=status)
        if teacher_id:
            queryset=queryset.filter(teacher=teacher_id)
        if course_id:
            queryset=queryset.filter(course=course_id)
        if lesson_days:
            queryset=queryset.filter(lessons_days_choice=lesson_days)
        
        return queryset
    
@extend_schema(tags=['Group'])
class GroupStatusUpdateAPIView(generics.UpdateAPIView):
    serializer_class = GroupStatusModelSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Group.objects.all()

    def perform_update(self, serializer):
        branch_id = serializer.validated_data.get('branch_id')
        status = serializer.validated_data.get('status')

        group = serializer.instance

        if status is not None:
            group.status = status

        if branch_id is not None:
            branch = Branch.objects.filter(id=branch_id).first()
            if not branch:
                raise ValidationError({'branch_id': "Branch topilmadi."})

            if not branch.courses.filter(id=group.course_id).exists():
                raise ValidationError({
                    'branch_id': "Ushbu branchda guruhga biriktirilgan kurs mavjud emas. Ko'chirish mumkin emas."
                })

            group.course.branch = branch_id
            group.course.save()

        group.save()


@extend_schema(tags=['Group'])
class GroupCreateAPIView(generics.CreateAPIView):
    queryset=Group.objects.all()
    serializer_class=GroupModelSerializer

@extend_schema(tags=['Group'])
class GroupDetailAPIView(generics.RetrieveAPIView):
    queryset=Group.objects.select_related('room','course')
    serializer_class=GroupDetailModelSerializer
    lookup_field='id'
