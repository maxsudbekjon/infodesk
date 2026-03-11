from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.pupil.models.note import StudentNote
from apps.pupil.models.student import StudnetTransfer, Student
from apps.pupil.serializers.student import (
    StudentChangeGroupSerializer,
    StudentNoteListSerializer,
    StudentRemoveFromGroupSerializer,
)

@extend_schema(tags=['Group'])
class StudentTransferCreateAPIView(generics.CreateAPIView):
    queryset = StudnetTransfer.objects.all()
    serializer_class = StudentChangeGroupSerializer

@extend_schema(tags=['Group'])
class StudentRemoveFromGroupAPIView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentRemoveFromGroupSerializer

@extend_schema(tags=['Group'])
class GroupStudentNoteListAPIView(generics.ListAPIView):
    serializer_class = StudentNoteListSerializer

    def get_queryset(self):
        group_id = self.kwargs.get("id")
        return (
            StudentNote.objects.filter(student__groups__id=group_id)
            .select_related("student", "operator__user")
            .order_by("-date")
        )
