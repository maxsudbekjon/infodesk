from django.core.exceptions import ValidationError
from rest_framework import generics
from apps.group.models.attendance import Attendance
from apps.group.serializers.attendance import AttendanceModelSerializer, GroupAttendanceModelSerializer
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework.pagination import PageNumberPagination

class AttendancePagination(PageNumberPagination):
    page_size = 20

@extend_schema(tags=['Group'])
class AttendanceCreateAPIView(generics.CreateAPIView):
    serializer_class = AttendanceModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Attendance.objects.select_related('group', 'student')

    def perform_create(self, serializer):
        student = serializer.validated_data.get('student')
        group = serializer.validated_data.get('group')

        if not group.students.filter(id=student.id).exists():
            raise ValidationError({'detail': 'This student not found in this group'})

        serializer.save()
        
@extend_schema(tags=['Group'])
class GroupAttendanceAPIView(generics.ListAPIView):
    serializer_class = GroupAttendanceModelSerializer
    pagination_class = AttendancePagination

    def get_queryset(self):
        group_id = self.kwargs["group_id"]

        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")

        qs = Attendance.objects.filter(group_id=group_id)

        if month and year:
            qs = qs.filter(date__year=year, date__month=month)

        return qs.select_related("student", "group").order_by("date")