from types import SimpleNamespace

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from datetime import time

from apps.group.choices import GROUP_DAYS_CHOICES
from apps.group.models.course import CourseTemplate
from apps.group.models.group import Group
from apps.group.models.score import GroupScore
from apps.pupil.admin import StudentAdmin
from apps.pupil.models import Student
from apps.settings.models import Branch, Organization
from apps.teacher.models import Teacher
from apps.user.choices import ROLE
from apps.user.models import User


class StudentAdminTests(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.admin = StudentAdmin(Student, AdminSite())

        self.owner = User.objects.create_user(
            phone_number="+998900200001",
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
            duration_months=3,
        )
        self.branch.courses.add(self.course)

        self.teacher_user = User.objects.create_user(
            phone_number="+998900200002",
            password="teacherpass123",
            full_name="Teacher User",
            role=ROLE.TEACHER,
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user, branch=self.branch)
        self.group = Group.objects.create(
            title="Math-1",
            course=self.course,
            branch=self.branch,
            teacher=self.teacher,
            lessons_days_choice=GROUP_DAYS_CHOICES.EVERAY_DAY,
            start_lesson=time(9, 0),
            end_lesson=time(10, 0),
        )

        self.student = Student.objects.create(
            full_name="Student One",
            phone_number="+998900200003",
            center=self.organization,
            group=self.group,
            used_coin=3,
        )

    def test_total_coin_is_editable_in_admin(self):
        request = self.request_factory.get("/admin/pupil/student/")

        self.assertNotIn("total_coin", self.admin.get_readonly_fields(request, self.student))

    def test_manual_total_coin_update_recalculates_offset(self):
        GroupScore.objects.create(
            group=self.group,
            student=self.student,
            score=10,
            reason="Initial coin",
        )
        self.student.refresh_from_db()
        self.assertEqual(self.student.total_coin, 7)

        request = self.request_factory.post("/admin/pupil/student/")
        form = SimpleNamespace(
            cleaned_data={"total_coin": 50},
            changed_data=["total_coin"],
        )

        self.admin.save_model(request, self.student, form, change=True)

        self.student.refresh_from_db()
        self.assertEqual(self.student.total_coin, 50)
        self.assertEqual(self.student.coin_offset, 43)

        GroupScore.objects.create(
            group=self.group,
            student=self.student,
            score=5,
            reason="Extra coin",
        )

        self.student.refresh_from_db()
        self.assertEqual(self.student.total_coin, 55)
