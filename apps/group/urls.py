from django.urls import path

from apps.group.views import (
    GroupCreateAPIView,
    GroupDeleteAPIView,
    GroupDetailAPIView,
    GroupListAPIView,
    GroupStatusUpdateAPIView,
    GroupUpdateAPIView,
)
from apps.group.views.attendance import (
    AttendanceCreateAPIView,
    GroupAttendanceAPIView,
    GroupMonthlyAttendanceAPIView,
)
from apps.group.views.exam import ExamCreateAPIView, GroupExamListAPIView
from apps.group.views.grade import GradeCreateAPIView, GroupGradeAPIView
from apps.group.views.note import GroupNoteCreateAPIView, GroupNoteListAPIView
from apps.group.views.discount import GroupDiscountCreateAPIView, GroupDiscountListAPIView
from apps.group.views.ranking import GroupRankingListAPIView
from apps.group.views.score import GroupScoreCreateAPIView, GroupScoreListAPIView
from apps.group.views.history import GroupHistoryCreateAPIView, GroupHistoryListAPIView
from apps.group.views.freeze import GroupFreezeCreateAPIView
from apps.group.views.student_ops import (
    GroupStudentNoteListAPIView,
    StudentRemoveFromGroupAPIView,
    StudentTransferCreateAPIView,
)
from apps.group.views.detail import GroupStudentAPIView

urlpatterns = [
    path('list/',GroupListAPIView.as_view(),name='group-list'),
    path('update-status&branch/<int:id>',GroupStatusUpdateAPIView.as_view(),name='group-status-update'),
    path('create/',GroupCreateAPIView.as_view(),name='group-create'),
    path('update/<int:id>', GroupUpdateAPIView.as_view(), name='group-update'),
    path('detail/<int:id>',GroupDetailAPIView.as_view(),name='group-detail'),
    path('delete/<int:id>', GroupDeleteAPIView.as_view(), name='group-delete'),
    path('attendance/',AttendanceCreateAPIView.as_view(),name='attendance-create'),
    path('grades/', GradeCreateAPIView.as_view(), name='grade-create'),
    path('group-student/<int:id>',GroupStudentAPIView.as_view(),name='group-student'),
    path('group-studnets-attendance/<int:id>',GroupAttendanceAPIView.as_view(),name='group-attendance'),
    path('group-students-attendance/<int:id>', GroupAttendanceAPIView.as_view(), name='group-attendance-v2'),
    path('group-monthly-attendance/<int:id>', GroupMonthlyAttendanceAPIView.as_view(), name='group-monthly-attendance'),
    path('group-students-grades/<int:id>', GroupGradeAPIView.as_view(), name='group-grades'),
    path('group-notes/create/', GroupNoteCreateAPIView.as_view(), name='group-note-create'),
    path('group-notes/<int:id>', GroupNoteListAPIView.as_view(), name='group-note-list'),
    path('exams/create/', ExamCreateAPIView.as_view(), name='exam-create'),
    path('group-exams/<int:id>', GroupExamListAPIView.as_view(), name='group-exam-list'),
    path('discounts/create/', GroupDiscountCreateAPIView.as_view(), name='group-discount-create'),
    path('group-discounts/<int:id>', GroupDiscountListAPIView.as_view(), name='group-discount-list'),
    path('group-ranking/<int:id>', GroupRankingListAPIView.as_view(), name='group-ranking'),
    path('group-scores/create/', GroupScoreCreateAPIView.as_view(), name='group-score-create'),
    path('group-scores/<int:id>', GroupScoreListAPIView.as_view(), name='group-score-list'),
    path('group-history/create/', GroupHistoryCreateAPIView.as_view(), name='group-history-create'),
    path('group-history/<int:id>', GroupHistoryListAPIView.as_view(), name='group-history-list'),
    path('group-freeze/create/', GroupFreezeCreateAPIView.as_view(), name='group-freeze-create'),
    path('student-transfer/create/', StudentTransferCreateAPIView.as_view(), name='student-transfer'),
    path('student-trasfer/create/', StudentTransferCreateAPIView.as_view(), name='student-trasfer'),
    path('student-remove-group/', StudentRemoveFromGroupAPIView.as_view(), name='student-remove-group'),
    path('group-student-notes/<int:id>', GroupStudentNoteListAPIView.as_view(), name='group-student-notes'),
]
