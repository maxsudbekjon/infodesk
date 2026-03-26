from datetime import date, time

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
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


class GroupRolePermissionTests(APITestCase):
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
        self.branch.courses.add(self.course)

        self.teacher_user = User.objects.create_user(
            phone_number="+998900000002",
            password="teacherpass123",
            role=ROLE.TEACHER,
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user, branch=self.branch)

        self.student_user = User.objects.create_user(
            phone_number="+998900000003",
            password="studentpass123",
            role=ROLE.STUDENT,
        )
        self.student = Student.objects.create(
            user=self.student_user,
            full_name="Student One",
            phone_number="+998900000003",
            center=self.organization,
            image=SimpleUploadedFile(
                "student-one.png",
                b"fake-image",
                content_type="image/png",
            ),
        )

        self.other_student = Student.objects.create(
            full_name="Student Two",
            phone_number="+998900000004",
            center=self.organization,
        )
        self.fk_only_student = Student.objects.create(
            full_name="Student Three",
            phone_number="+998900000005",
            center=self.organization,
        )

        self.group = Group.objects.create(
            title="Math-1",
            course=self.course,
            branch=self.branch,
            teacher=self.teacher,
            lessons_days_choice=GROUP_DAYS_CHOICES.ODD_DAYS,
            start_lesson=time(9, 0),
            end_lesson=time(10, 0),
        )
        self.group.students.add(self.student, self.other_student)
        self.student.group = self.group
        self.student.save(update_fields=["group"])
        self.other_student.group = self.group
        self.other_student.save(update_fields=["group"])
        self.fk_only_student.group = self.group
        self.fk_only_student.save(update_fields=["group"])

        Attendance.objects.create(
            group=self.group,
            student=self.student,
            date=date(2026, 3, 20),
            is_present=True,
        )
        Attendance.objects.create(
            group=self.group,
            student=self.other_student,
            date=date(2026, 3, 20),
            is_present=False,
        )
        Grade.objects.create(
            group=self.group,
            student=self.student,
            date=date(2026, 3, 20),
            grade=5,
        )
        Grade.objects.create(
            group=self.group,
            student=self.other_student,
            date=date(2026, 3, 20),
            grade=3,
        )
        GroupScore.objects.create(
            group=self.group,
            student=self.student,
            score=10,
            reason="Excellent",
        )
        GroupScore.objects.create(
            group=self.group,
            student=self.other_student,
            score=4,
            reason="Late",
        )

    def test_teacher_can_create_attendance_for_owned_group(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.post(
            reverse("attendance-create"),
            {
                "group": self.group.id,
                "student": self.student.id,
                "date": "2026-03-21",
                "is_present": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_cannot_create_attendance(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(
            reverse("attendance-create"),
            {
                "group": self.group.id,
                "student": self.student.id,
                "date": "2026-03-21",
                "is_present": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_sees_only_own_attendance(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("group-attendance", kwargs={"id": self.group.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["student"], self.student.id)

    def test_student_sees_only_own_grades(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("group-grades", kwargs={"id": self.group.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["student"], self.student.id)

    def test_student_sees_only_own_scores(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("group-score-list", kwargs={"id": self.group.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["student"], self.student.id)

    def test_teacher_can_list_students_of_group_by_id(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.get(reverse("group-student", kwargs={"id": self.group.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.group.id)
        students = response.data["students"]
        self.assertEqual(len(students), 3)
        self.assertSetEqual(
            {student["id"] for student in students},
            {self.student.id, self.other_student.id, self.fk_only_student.id},
        )
        student_data = next(item for item in students if item["id"] == self.student.id)
        self.assertIsNotNone(student_data["image"])
        self.assertIn("student-avatar", student_data["image"])

    def test_group_ranking_returns_student_cards_with_image(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.get(reverse("group-ranking", kwargs={"id": self.group.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 3)

        first = results[0]
        self.assertEqual(first["rating"], 1)
        self.assertEqual(first["full_name"], self.student.full_name)
        self.assertEqual(first["total_grade"], 5)
        self.assertIsNotNone(first["image"])
        self.assertIn("student-avatar", first["image"])
