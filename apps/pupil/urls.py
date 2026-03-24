from django.urls import path

from apps.pupil.views import StudentNoteCreateAPIView, StudentReturnToLeadAPIView



urlpatterns = [
    path('student-return-lead/', StudentReturnToLeadAPIView.as_view(), name='student-return-lead'),
    path('student-note/create/', StudentNoteCreateAPIView.as_view(), name='student-note-create'),
]
