from datetime import time, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.group.choices import GROUP_DAYS_CHOICES
from apps.group.models import CourseTemplate, Day, Group
from apps.pupil.models import Student
from apps.settings.models import Branch, Organization
from apps.teacher.models import Teacher
from apps.user.choices import ROLE
from apps.user.models import User


class TeacherCourseGroupsEndpointTests(APITestCase):
    def setUp(self):
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        self.owner = User.objects.create_user(
            phone_number="+998900000001",
            password="ownerpass123",
            full_name="Owner User",
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
        self.course_english = CourseTemplate.objects.create(
            name="English",
            center=self.organization,
            duration_months=6,
        )
        self.branch.courses.add(self.course_math, self.course_english)

        self.today_day = Day.objects.create(day=today.strftime("%A"))
        self.tomorrow_day = Day.objects.create(day=tomorrow.strftime("%A"))

        self.group_1_m2m_student = Student.objects.create(
            full_name="Math Student 1",
            phone_number="+998900000010",
            center=self.organization,
        )
        self.group_1_fk_only_student = Student.objects.create(
            full_name="Math Student 2",
            phone_number="+998900000011",
            center=self.organization,
        )
        self.group_2_student = Student.objects.create(
            full_name="English Student",
            phone_number="+998900000012",
            center=self.organization,
        )

        self.teacher_user = User.objects.create_user(
            phone_number="+998900000002",
            password="teacherpass123",
            full_name="Teacher User",
            role=ROLE.TEACHER,
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            branch=self.branch,
        )

        self.other_teacher_user = User.objects.create_user(
            phone_number="+998900000003",
            password="teacherpass123",
            full_name="Other Teacher",
            role=ROLE.TEACHER,
        )
        self.other_teacher = Teacher.objects.create(
            user=self.other_teacher_user,
            branch=self.branch,
        )

        self.teacher_group_1 = Group.objects.create(
            title="Math-1",
            course=self.course_math,
            branch=self.branch,
            teacher=self.teacher,
            lessons_days_choice=GROUP_DAYS_CHOICES.ODD_DAYS,
            start_lesson=time(9, 0),
            end_lesson=time(10, 0),
        )
        self.teacher_group_1.lessons_days.add(self.today_day)
        self.teacher_group_1.students.add(self.group_1_m2m_student)
        self.group_1_fk_only_student.group = self.teacher_group_1
        self.group_1_fk_only_student.save(update_fields=["group"])

        self.teacher_group_2 = Group.objects.create(
            title="English-1",
            course=self.course_english,
            branch=self.branch,
            teacher=self.teacher,
            lessons_days_choice=GROUP_DAYS_CHOICES.EVEN_DAYS,
            start_lesson=time(10, 0),
            end_lesson=time(11, 0),
        )
        self.teacher_group_2.lessons_days.add(self.tomorrow_day)
        self.teacher_group_2.students.add(self.group_2_student)
        self.other_teacher_group = Group.objects.create(
            title="Other-1",
            course=self.course_math,
            branch=self.branch,
            teacher=self.other_teacher,
            lessons_days_choice=GROUP_DAYS_CHOICES.EVERAY_DAY,
            start_lesson=time(11, 0),
            end_lesson=time(12, 0),
        )

    def _results(self, response):
        if isinstance(response.data, dict):
            return response.data.get("results", response.data)
        return response.data

    def test_logged_in_teacher_can_fetch_groups_without_course_id(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.get("/apps/teachers/my-courses/groups/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._results(response)
        self.assertEqual(len(results), 2)
        self.assertSetEqual(
            {item["id"] for item in results},
            {self.teacher_group_1.id, self.teacher_group_2.id},
        )
        first_group = next(item for item in results if item["id"] == self.teacher_group_1.id)
        second_group = next(item for item in results if item["id"] == self.teacher_group_2.id)

        self.assertEqual(first_group["title"], "Math-1")
        self.assertEqual(first_group["lessons_days"], [self.today_day.day])
        self.assertEqual(first_group["start_lesson"], "09:00:00")
        self.assertEqual(first_group["end_lesson"], "10:00:00")
        self.assertEqual(first_group["duration_months"], 3)
        self.assertEqual(first_group["total_student"], 2)
        self.assertTrue(first_group["attendance_today"])

        self.assertEqual(second_group["title"], "English-1")
        self.assertEqual(second_group["lessons_days"], [self.tomorrow_day.day])
        self.assertEqual(second_group["duration_months"], 6)
        self.assertEqual(second_group["total_student"], 1)
        self.assertFalse(second_group["attendance_today"])

    def test_logged_in_teacher_can_still_filter_groups_by_course_id(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.get(
            f"/apps/teachers/my-courses/{self.course_math.id}/groups/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.teacher_group_1.id)
        self.assertEqual(results[0]["duration_months"], 3)
        self.assertEqual(results[0]["total_student"], 2)
