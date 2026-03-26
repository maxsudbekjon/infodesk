from datetime import timedelta, time
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.group.choices import GROUP_DAYS_CHOICES
from apps.group.models.attendance import Attendance
from apps.group.models.course import CourseTemplate
from apps.group.models.group import Group
from apps.group.models.score import GroupScore
from apps.pupil.models import Student
from apps.settings.models import Branch, Organization
from apps.teacher.models import Teacher
from apps.user.choices import ROLE
from apps.user.models import User


class StudentDashboardTests(APITestCase):
    def setUp(self):
        self.today = timezone.localdate()

        self.owner = User.objects.create_user(
            phone_number="+998900100001",
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
        self.course_math = CourseTemplate.objects.create(
            name="Math",
            center=self.organization,
        )
        self.course_science = CourseTemplate.objects.create(
            name="Science",
            center=self.organization,
        )
        self.branch.courses.add(self.course_math, self.course_science)

        self.teacher_user = User.objects.create_user(
            phone_number="+998900100002",
            password="teacherpass123",
            role=ROLE.TEACHER,
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user, branch=self.branch)

        self.student_user = User.objects.create_user(
            phone_number="+998900100003",
            password="studentpass123",
            role=ROLE.STUDENT,
        )
        self.student = Student.objects.create(
            user=self.student_user,
            full_name="Student One",
            phone_number="+998900100003",
            center=self.organization,
        )

        self.math_group = Group.objects.create(
            title="Math-1",
            course=self.course_math,
            branch=self.branch,
            teacher=self.teacher,
            lessons_days_choice=GROUP_DAYS_CHOICES.EVERAY_DAY,
            start_lesson=time(9, 0),
            end_lesson=time(10, 0),
        )
        self.science_group = Group.objects.create(
            title="Science-1",
            course=self.course_science,
            branch=self.branch,
            teacher=self.teacher,
            lessons_days_choice=GROUP_DAYS_CHOICES.EVERAY_DAY,
            start_lesson=time(10, 0),
            end_lesson=time(11, 0),
        )

        self.math_group.students.add(self.student)
        self.science_group.students.add(self.student)
        self.student.group = self.math_group
        self.student.save(update_fields=["group"])

        Attendance.objects.create(
            group=self.math_group,
            student=self.student,
            date=self.today,
            is_present=True,
        )
        Attendance.objects.create(
            group=self.math_group,
            student=self.student,
            date=self.today - timedelta(days=1),
            is_present=False,
        )
        Attendance.objects.create(
            group=self.science_group,
            student=self.student,
            date=self.today - timedelta(days=2),
            is_present=True,
        )
        Attendance.objects.create(
            group=self.science_group,
            student=self.student,
            date=self.today - timedelta(days=3),
            is_present=False,
        )
        Attendance.objects.create(
            group=self.science_group,
            student=self.student,
            date=self.today - timedelta(days=4),
            is_present=False,
        )

        GroupScore.objects.create(
            group=self.math_group,
            student=self.student,
            score=7,
            reason="Math bonus",
        )
        GroupScore.objects.create(
            group=self.math_group,
            student=self.student,
            score=5,
            reason="Math bonus 2",
        )
        GroupScore.objects.create(
            group=self.science_group,
            student=self.student,
            score=3,
            reason="Science bonus",
        )

    def test_student_course_summary(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("student-my-courses"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        courses = response.data["courses"]
        self.assertEqual(len(courses), 2)

        math_row = next(item for item in courses if item["course_name"] == "Math")
        self.assertEqual(math_row["course_id"], self.course_math.id)
        self.assertEqual(math_row["present_count"], 1)
        self.assertEqual(math_row["absent_count"], 1)
        self.assertEqual(math_row["coin"], 12)

        science_row = next(item for item in courses if item["course_name"] == "Science")
        self.assertEqual(science_row["course_id"], self.course_science.id)
        self.assertEqual(science_row["present_count"], 1)
        self.assertEqual(science_row["absent_count"], 2)
        self.assertEqual(science_row["coin"], 3)

    def test_student_monthly_attendance(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("student-my-attendance", kwargs={"group_id": self.math_group.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["month"], self.today.month)
        self.assertEqual(response.data["year"], self.today.year)

        students = response.data["students"]
        self.assertEqual(len(students), 1)
        row = students[0]
        self.assertEqual(row["id"], self.student.id)
        self.assertEqual(row["full_name"], self.student.full_name)
        self.assertEqual(row["coin"], 12)

        attendance_days = {item["day"]: item["is_present"] for item in row["attendance_days"]}
        self.assertTrue(attendance_days[self.today.day])
        self.assertFalse(attendance_days[(self.today - timedelta(days=1)).day])
