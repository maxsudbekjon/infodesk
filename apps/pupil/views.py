from rest_framework import generics
from apps.pupil.models.student import Student
from apps.pupil.models.note import StudentNote
from apps.pupil.serializers.student import (
    StudentNoteCreateSerializer,
    StudentReturnToLeadSerializer,
)
# Create your views here.

class StudentReturnToLeadAPIView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentReturnToLeadSerializer


class StudentNoteCreateAPIView(generics.CreateAPIView):
    queryset = StudentNote.objects.all()
    serializer_class = StudentNoteCreateSerializer
