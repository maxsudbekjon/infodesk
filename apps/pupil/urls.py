from django.urls import path

from apps.pupil.views import (
    StudentCourseSummaryAPIView,
    StudentGroupListAPIView,
    StudentNoteCreateAPIView,
    StudentMonthlyAttendanceAPIView,
    StudentReturnToLeadAPIView,
)



urlpatterns = [
    path('my-groups/', StudentGroupListAPIView.as_view(), name='student-my-groups'),
    path('my-courses/', StudentCourseSummaryAPIView.as_view(), name='student-my-courses'),
    path('my-attendance/<int:group_id>/', StudentMonthlyAttendanceAPIView.as_view(), name='student-my-attendance'),
    path('student-return-lead/', StudentReturnToLeadAPIView.as_view(), name='student-return-lead'),
    path('student-note/create/', StudentNoteCreateAPIView.as_view(), name='student-note-create'),
]
