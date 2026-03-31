from django.urls import path

from apps.pupil.views import (
    StudentCourseSummaryAPIView,
    StudentGroupListAPIView,
    StudentMeAPIView,
    StudentNoteCreateAPIView,
    StudentMonthlyAttendanceAPIView,
    StudentTodayCoinAPIView,
    StudentReturnToLeadAPIView,
)



urlpatterns = [
    path('me/', StudentMeAPIView.as_view(), name='student-me'),
    path('my-groups/', StudentGroupListAPIView.as_view(), name='student-my-groups'),
    path('my-courses/', StudentCourseSummaryAPIView.as_view(), name='student-my-courses'),
    path('my-today-coins/', StudentTodayCoinAPIView.as_view(), name='student-my-today-coins'),
    path('my-attendance/<int:group_id>/', StudentMonthlyAttendanceAPIView.as_view(), name='student-my-attendance'),
    path('student-return-lead/', StudentReturnToLeadAPIView.as_view(), name='student-return-lead'),
    path('student-note/create/', StudentNoteCreateAPIView.as_view(), name='student-note-create'),
]
