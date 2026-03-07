from rest_framework import generics

from apps.pupil.models.note import StudentNote
from apps.pupil.models.student import StudnetTransfer, Student
from apps.pupil.serializers.student import (
    StudentChangeGroupSerializer,
    StudentNoteListSerializer,
    StudentRemoveFromGroupSerializer,
)


class StudentTransferCreateAPIView(generics.CreateAPIView):
    queryset = StudnetTransfer.objects.all()
    serializer_class = StudentChangeGroupSerializer


class StudentRemoveFromGroupAPIView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentRemoveFromGroupSerializer


class GroupStudentNoteListAPIView(generics.ListAPIView):
    serializer_class = StudentNoteListSerializer

    def get_queryset(self):
        group_id = self.kwargs.get("id")
        return (
            StudentNote.objects.filter(student__groups__id=group_id)
            .select_related("student", "operator__user")
            .order_by("-date")
        )
