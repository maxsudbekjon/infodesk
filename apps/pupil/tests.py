from datetime import date, timedelta, time
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.group.choices import GROUP_DAYS_CHOICES
from apps.group.models.attendance import Attendance
from apps.group.models.course import CourseTemplate
from apps.group.models.grade import Grade
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
            duration_months=3,
        )
        self.course_science = CourseTemplate.objects.create(
            name="Science",
            center=self.organization,
            duration_months=6,
        )
        self.branch.courses.add(self.course_math, self.course_science)

        self.teacher_user = User.objects.create_user(
            phone_number="+998900100002",
            password="teacherpass123",
            full_name="Teacher User",
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

        self.today_math_attendance = Attendance.objects.create(
            group=self.math_group,
            student=self.student,
            date=self.today,
            is_present=True,
        )
        self.previous_day_math_attendance = Attendance.objects.create(
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
        Grade.objects.create(
            group=self.math_group,
            student=self.student,
            date=self.today,
            grade=5,
        )
        Grade.objects.create(
            group=self.science_group,
            student=self.student,
            date=self.today - timedelta(days=1),
            grade=4,
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

    def test_student_course_summary_skips_unmarked_attendance(self):
        Attendance.objects.create(
            group=self.math_group,
            student=self.student,
            date=self.today - timedelta(days=5),
            is_present=None,
        )
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("student-my-courses"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        math_row = next(item for item in response.data["courses"] if item["course_name"] == "Math")
        self.assertEqual(math_row["present_count"], 1)
        self.assertEqual(math_row["absent_count"], 1)

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

        attendance_days = {item["day"]: item for item in row["attendance_days"]}
        self.assertTrue(attendance_days[self.today.day]["is_present"])
        self.assertEqual(attendance_days[self.today.day]["id"], self.today_math_attendance.id)
        self.assertFalse(attendance_days[(self.today - timedelta(days=1)).day]["is_present"])
        self.assertEqual(
            attendance_days[(self.today - timedelta(days=1)).day]["id"],
            self.previous_day_math_attendance.id,
        )

    def test_student_can_list_own_groups(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("student-my-groups"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        groups = response.data["groups"]
        self.assertEqual(len(groups), 2)
        self.assertSetEqual(
            {item["id"] for item in groups},
            {self.math_group.id, self.science_group.id},
        )

        math_row = next(item for item in groups if item["id"] == self.math_group.id)
        self.assertEqual(math_row["title"], self.math_group.title)
        self.assertEqual(math_row["course_id"], self.course_math.id)
        self.assertEqual(math_row["course_name"], self.course_math.name)
        self.assertEqual(math_row["duration_months"], self.course_math.duration_months)
        self.assertEqual(math_row["branch_id"], self.branch.id)
        self.assertEqual(math_row["branch_name"], self.branch.name)
        self.assertEqual(math_row["teacher_id"], self.teacher.id)
        self.assertEqual(math_row["teacher_name"], self.teacher_user.full_name)
        self.assertEqual(math_row["room"], None)
        self.assertEqual(math_row["lessons_days"], [])
        self.assertEqual(math_row["lessons_days_choice"], GROUP_DAYS_CHOICES.EVERAY_DAY)
        self.assertEqual(math_row["total_student"], 1)

        science_row = next(item for item in groups if item["id"] == self.science_group.id)
        self.assertEqual(science_row["course_id"], self.course_science.id)
        self.assertEqual(science_row["course_name"], self.course_science.name)
        self.assertEqual(science_row["duration_months"], self.course_science.duration_months)
        self.assertEqual(science_row["teacher_id"], self.teacher.id)
        self.assertEqual(science_row["total_student"], 1)

    def test_teacher_cannot_list_student_groups_endpoint(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.get(reverse("student-my-groups"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_list_today_coins_with_ids(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("student-my-today-coins"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["date"]), str(self.today))
        self.assertEqual(response.data["total_coin"], 15)
        self.assertEqual(len(response.data["coins"]), 3)

        coin_ids = {item["id"] for item in response.data["coins"]}
        expected_ids = set(
            GroupScore.objects.filter(student=self.student).values_list("id", flat=True)
        )
        self.assertSetEqual(coin_ids, expected_ids)

        first_coin = response.data["coins"][0]
        self.assertIn("group_id", first_coin)
        self.assertIn("group_title", first_coin)
        self.assertIn("course_id", first_coin)
        self.assertIn("course_name", first_coin)
        self.assertIn("score", first_coin)
        self.assertIn("reason", first_coin)
        self.assertIn("created_at", first_coin)

    def test_student_can_view_profile(self):
        self.student_user.birthday = date(2000, 10, 30)
        self.student_user.save(update_fields=["birthday"])
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("student-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.student.id)
        self.assertEqual(response.data["full_name"], self.student.full_name)
        self.assertEqual(response.data["phone_number"], self.student.phone_number)
        self.assertEqual(str(response.data["birth_date"]), "2000-10-30")
        self.assertEqual(str(response.data["enrollment_date"]), str(self.student.created_at.date()))
        self.assertEqual(response.data["average_grade_percent"], 90)
        self.assertEqual(response.data["attendance_percent"], 40)
        self.assertEqual(response.data["total_coin"], 15)
        self.assertEqual(response.data["earned_coin"], 15)
        self.assertEqual(response.data["used_coin"], 0)
        self.assertEqual(response.data["course_count"], 2)
        self.assertEqual(len(response.data["active_courses"]), 2)

        math_row = next(item for item in response.data["active_courses"] if item["group_id"] == self.math_group.id)
        self.assertEqual(math_row["course_id"], self.course_math.id)
        self.assertEqual(math_row["course_name"], self.course_math.name)
        self.assertEqual(math_row["teacher_id"], self.teacher.id)
        self.assertEqual(math_row["teacher_name"], self.teacher_user.full_name)
        self.assertEqual(math_row["progress_percent"], 50)

        science_row = next(item for item in response.data["active_courses"] if item["group_id"] == self.science_group.id)
        self.assertEqual(science_row["course_id"], self.course_science.id)
        self.assertEqual(science_row["progress_percent"], 33)

    def test_teacher_cannot_view_student_profile(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.get(reverse("student-me"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
