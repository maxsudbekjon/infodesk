from pathlib import Path
from datetime import time
import sys

from django.test import TestCase

from apps.group.choices import GROUP_DAYS_CHOICES
from apps.group.models import CourseTemplate, Group, GroupScore
from apps.settings.models import Branch, Organization
from apps.pupil.models import Student
from apps.pupil.coin import IMPORT_SCORE_REASON
from apps.user.choices import ROLE
from apps.user.models import User


EXCEL_IMPORT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "excel_import"
if str(EXCEL_IMPORT_PATH) not in sys.path:
    sys.path.insert(0, str(EXCEL_IMPORT_PATH))

from import_student import _sync_import_coin, find_existing_student  # noqa: E402


class ImportStudentMatchingTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            phone_number="+998900000001",
            password="ownerpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.owner,
            name="Org",
            latitude=41,
            longitude=69,
        )
        self.branch = Branch.objects.create(
            organization=self.organization,
            name="Main branch",
            latitude=41,
            longitude=69,
        )
        self.course = CourseTemplate.objects.create(
            name="Math",
            center=self.organization,
        )
        self.group = Group.objects.create(
            title="Math-1",
            course=self.course,
            branch=self.branch,
            lessons_days_choice=GROUP_DAYS_CHOICES.ODD_DAYS,
            start_lesson=time(9, 0),
            end_lesson=time(10, 0),
        )

    def test_find_existing_student_matches_user_secondary_phone(self):
        student_user = User.objects.create_user(
            phone_number="+998901234567",
            phone_number2="+998907654321",
            password="studentpass123",
            full_name="Ali Valiyev",
            role=ROLE.STUDENT,
        )
        student = Student.objects.create(
            user=student_user,
            full_name="Ali Valiyev",
            center=self.organization,
            group=self.group,
        )

        matched_student = find_existing_student(
            None,
            "Ali Valiyev",
            "+998907654321",
            self.group,
        )

        self.assertEqual(matched_student, student)

    def test_find_existing_student_matches_reversed_full_name_inside_group(self):
        student = Student.objects.create(
            full_name="Ali Valiyev",
            phone_number="+998909999999",
            center=self.organization,
            group=self.group,
        )

        matched_student = find_existing_student(
            None,
            "Valiyev Ali",
            None,
            self.group,
        )

        self.assertEqual(matched_student, student)

    def test_sync_import_coin_sets_current_balance_even_with_used_coin(self):
        student = Student.objects.create(
            full_name="Ali Valiyev",
            phone_number="+998909999999",
            center=self.organization,
            group=self.group,
            used_coin=459,
        )

        _sync_import_coin(student, self.group, 459)
        student.refresh_from_db()

        self.assertEqual(student.total_coin, 459)
        self.assertEqual(student.coin_offset, 918)
        self.assertFalse(
            GroupScore.objects.filter(student=student, reason=IMPORT_SCORE_REASON).exists()
        )

    def test_sync_import_coin_replaces_old_import_scores_with_coin_offset(self):
        other_group = Group.objects.create(
            title="Math-2",
            course=self.course,
            branch=self.branch,
            lessons_days_choice=GROUP_DAYS_CHOICES.EVEN_DAYS,
            start_lesson=time(10, 0),
            end_lesson=time(11, 0),
        )
        student = Student.objects.create(
            full_name="Ali Valiyev",
            phone_number="+998909999998",
            center=self.organization,
            group=self.group,
        )
        GroupScore.objects.create(
            student=student,
            group=self.group,
            score=300,
            reason=IMPORT_SCORE_REASON,
        )
        GroupScore.objects.create(
            student=student,
            group=other_group,
            score=300,
            reason=IMPORT_SCORE_REASON,
        )
        GroupScore.objects.create(
            student=student,
            group=self.group,
            score=25,
            reason="Manual reward",
        )

        _sync_import_coin(student, self.group, 400)
        student.refresh_from_db()

        self.assertEqual(student.total_coin, 400)
        self.assertEqual(student.coin_offset, 375)
        self.assertEqual(
            GroupScore.objects.filter(student=student, reason=IMPORT_SCORE_REASON).count(),
            0,
        )
