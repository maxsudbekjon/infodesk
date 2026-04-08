import json
from datetime import date, time

from django.test import Client, TestCase
from django.urls import reverse

from apps.group.choices import GROUP_DAYS_CHOICES
from apps.group.models import Attendance, CourseTemplate, Group
from apps.pupil.models import Student
from apps.settings.models import Branch, Organization
from apps.teacher.models import Teacher
from apps.user.models import User


class GroupAdminAttendanceTests(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST="127.0.0.1")
        self.admin_user = User.objects.create_superuser(
            phone_number="+998900300001",
            password="adminpass123",
            full_name="Admin User",
        )
        self.client.force_login(self.admin_user)

        self.owner = User.objects.create_user(
            phone_number="+998900300002",
            password="ownerpass123",
        )
        self.organization = Organization.objects.create(
            owner=self.owner,
            name="Demo center",
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
        self.teacher = Teacher.objects.create(branch=self.branch)
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
            phone_number="+998900300003",
            center=self.organization,
            group=self.group,
        )

    def test_group_overview_renders_clickable_attendance_cells(self):
        response = self.client.get(reverse("admin:group_group_overview", args=[self.group.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-attendance-cell', html=False)
        self.assertContains(response, reverse("admin:group_attendance_update"))

    def test_admin_can_update_attendance_state(self):
        target_date = date(2026, 4, 10)
        url = reverse("admin:group_attendance_update")

        for state, expected in (("present", True), ("absent", False), ("neutral", None)):
            response = self.client.post(
                url,
                data=json.dumps(
                    {
                        "group_id": self.group.pk,
                        "student_id": self.student.pk,
                        "date": target_date.isoformat(),
                        "state": state,
                    }
                ),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["state"], state)
            attendance = Attendance.objects.get(
                group=self.group,
                student=self.student,
                date=target_date,
            )
            self.assertEqual(attendance.is_present, expected)
