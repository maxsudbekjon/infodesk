from types import SimpleNamespace

from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import Client
from django.test import RequestFactory, TestCase
from datetime import time
from django.urls import reverse

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
        self.client = Client(HTTP_HOST="127.0.0.1")

        self.admin_user = User.objects.create_superuser(
            phone_number="+998900299999",
            password="adminpass123",
            full_name="Admin User",
        )
        self.client.force_login(self.admin_user)

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

    def _build_post_request(self):
        request = self.request_factory.post("/admin/pupil/student/")
        setattr(request, "session", self.client.session)
        storage = FallbackStorage(request)
        setattr(request, "_messages", storage)
        request.user = self.owner
        return request

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

        request = self._build_post_request()
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

    def test_admin_form_accepts_active_status_alias(self):
        request = self.request_factory.post("/admin/pupil/student/add/")
        form_class = self.admin.get_form(request)
        form = form_class(
            data={
                "full_name": "Alias Student",
                "phone_number": "+998900200099",
                "center": self.organization.pk,
                "group": self.group.pk,
                "status": "active",
                "payment_status": "debtor",
                "balance": "0",
                "used_coin": "0",
                "total_coin": "0",
                "coin_offset": "0",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["status"], "avtive")

    def test_admin_form_rejects_add_coin_above_limit(self):
        request = self.request_factory.post("/admin/pupil/student/add/")
        form_class = self.admin.get_form(request)
        form = form_class(
            data={
                "full_name": "Coin Limit Student",
                "phone_number": "+998900200100",
                "center": self.organization.pk,
                "group": self.group.pk,
                "status": "avtive",
                "payment_status": "debtor",
                "balance": "0",
                "used_coin": "0",
                "total_coin": "0",
                "coin_offset": "0",
                "add_coin": "151",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("add_coin", form.errors)

    def test_save_model_can_add_coin_with_limit(self):
        GroupScore.objects.create(
            group=self.group,
            student=self.student,
            score=10,
            reason="Initial coin",
        )
        self.student.refresh_from_db()
        self.assertEqual(self.student.total_coin, 7)

        request = self._build_post_request()
        form = SimpleNamespace(
            cleaned_data={"total_coin": self.student.total_coin, "add_coin": 150, "remove_coin": 0},
            changed_data=["add_coin"],
        )

        self.admin.save_model(request, self.student, form, change=True)

        self.student.refresh_from_db()
        self.assertEqual(self.student.total_coin, 157)
        self.assertEqual(self.student.coin_offset, 150)

    def test_save_model_can_remove_coin_without_limit(self):
        GroupScore.objects.create(
            group=self.group,
            student=self.student,
            score=10,
            reason="Initial coin",
        )
        self.student.refresh_from_db()
        self.assertEqual(self.student.total_coin, 7)

        request = self._build_post_request()
        form = SimpleNamespace(
            cleaned_data={"total_coin": self.student.total_coin, "add_coin": 0, "remove_coin": 999},
            changed_data=["remove_coin"],
        )

        self.admin.save_model(request, self.student, form, change=True)

        self.student.refresh_from_db()
        self.assertEqual(self.student.total_coin, 0)
        self.assertEqual(self.student.coin_offset, -7)

    def test_attendance_view_shows_current_total_coin(self):
        GroupScore.objects.create(
            group=self.group,
            student=self.student,
            score=55,
            reason="Monthly coin",
        )
        self.student.coin_offset = 153
        self.student.total_coin = 205
        self.student.save(update_fields=["coin_offset", "total_coin"])

        response = self.client.get(f"/admin/pupil/student/{self.student.pk}/attendance/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["student_attendance"]["summary"]["coin_total"], 205)
        self.assertEqual(response.context["student_attendance"]["group_rows"][0]["coin"], 205)
        self.assertEqual(response.context["student_attendance"]["group_rows"][0]["monthly_coin"], 55)

    def test_quick_coin_update_adds_with_limit(self):
        response = self.client.post(
            reverse("admin:pupil_student_coin_update", args=[self.student.pk]),
            {"action": "add", "amount": 150},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.total_coin, 150)
        self.assertEqual(response.json()["total_coin"], 150)

    def test_quick_coin_update_rejects_large_add(self):
        response = self.client.post(
            reverse("admin:pupil_student_coin_update", args=[self.student.pk]),
            {"action": "add", "amount": 151},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        self.student.refresh_from_db()
        self.assertEqual(self.student.total_coin, 0)

    def test_quick_coin_update_removes_without_limit(self):
        self.student.total_coin = 80
        self.student.coin_offset = 80
        self.student.save(update_fields=["total_coin", "coin_offset"])

        response = self.client.post(
            reverse("admin:pupil_student_coin_update", args=[self.student.pk]),
            {"action": "remove", "amount": 1000},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.total_coin, 0)
