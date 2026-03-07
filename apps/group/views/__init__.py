from .list import GroupListAPIView
from .status_update import GroupStatusUpdateAPIView
from .create import GroupCreateAPIView
from .detail import GroupDetailAPIView
from .update import GroupUpdateAPIView
from .delete import GroupDeleteAPIView
from .student_ops import (
    GroupStudentNoteListAPIView,
    StudentRemoveFromGroupAPIView,
    StudentTransferCreateAPIView,
)
from .attendance import AttendanceCreateAPIView
from .grade import GroupGradeAPIView
from .note import GroupNoteCreateAPIView, GroupNoteListAPIView
from .exam import ExamCreateAPIView, GroupExamListAPIView
from .discount import GroupDiscountCreateAPIView, GroupDiscountListAPIView
from .ranking import GroupRankingListAPIView
from .score import GroupScoreCreateAPIView
from .history import GroupHistoryCreateAPIView, GroupHistoryListAPIView
from .freeze import GroupFreezeCreateAPIView
