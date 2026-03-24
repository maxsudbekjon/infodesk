from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.pupil.models import Student
from apps.user.choices import ROLE
from apps.user.models import User


class UserLoginAPITests(APITestCase):
    def test_teacher_can_login_and_receives_role_payload(self):
        user = User.objects.create_user(
            phone_number="+998901234567",
            password="secret123",
            full_name="Teacher User",
            role=ROLE.TEACHER,
        )

        from apps.teacher.models import Teacher

        Teacher.objects.create(user=user)

        response = self.client.post(
            reverse("user-login"),
            {"phone_number": "+998901234567", "password": "secret123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["role"], ROLE.TEACHER)
        self.assertIsNotNone(response.data["user"]["teacher_id"])

    def test_student_login_auto_links_student_profile_by_phone(self):
        user = User.objects.create_user(
            phone_number="+998909998877",
            password="secret123",
            full_name="Student User",
            role=ROLE.STUDENT,
        )
        student = Student.objects.create(
            full_name="Student User",
            phone_number="+998909998877",
        )

        response = self.client.post(
            reverse("user-login"),
            {"phone_number": "+998909998877", "password": "secret123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        student.refresh_from_db()
        self.assertEqual(student.user_id, user.id)
        self.assertEqual(response.data["user"]["role"], ROLE.STUDENT)
        self.assertEqual(response.data["user"]["student_id"], student.id)

    def test_non_teacher_or_student_cannot_login(self):
        User.objects.create_user(
            phone_number="+998900001122",
            password="secret123",
            role=ROLE.ADMIN,
        )

        response = self.client.post(
            reverse("user-login"),
            {"phone_number": "+998900001122", "password": "secret123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
