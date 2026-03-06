from django.core.exceptions import ValidationError
from rest_framework import generics
from apps.group.models.attendance import Attendance
from apps.group.serializers.attendance import AttendanceModelSerializer
from rest_framework.permissions import IsAuthenticated



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