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

    def test_teacher_login_falls_back_to_first_and_last_name(self):
        user = User.objects.create_user(
            phone_number="+998901234568",
            password="secret123",
            first_name="Teacher",
            last_name="User",
            role=ROLE.TEACHER,
        )

        from apps.teacher.models import Teacher

        Teacher.objects.create(user=user)

        response = self.client.post(
            reverse("user-login"),
            {"phone_number": "+998901234568", "password": "secret123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["full_name"], "Teacher User")

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

    def test_teacher_can_change_password(self):
        user = User.objects.create_user(
            phone_number="+998901111111",
            password="oldpass123",
            role=ROLE.TEACHER,
        )
        from apps.teacher.models import Teacher

        Teacher.objects.create(user=user)
        self.client.force_authenticate(user=user)

        response = self.client.post(
            reverse("user-change-password"),
            {
                "old_password": "oldpass123",
                "new_password": "newpass12345",
                "new_password_confirm": "newpass12345",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("newpass12345"))
        self.assertFalse(user.check_password("oldpass123"))

    def test_student_can_change_password(self):
        user = User.objects.create_user(
            phone_number="+998902222222",
            password="oldpass123",
            role=ROLE.STUDENT,
        )
        Student.objects.create(
            user=user,
            full_name="Student User",
            phone_number="+998902222222",
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            reverse("user-change-password"),
            {
                "old_password": "oldpass123",
                "new_password": "studentnew123",
                "new_password_confirm": "studentnew123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("studentnew123"))

    def test_change_password_fails_when_old_password_is_wrong(self):
        user = User.objects.create_user(
            phone_number="+998903333333",
            password="oldpass123",
            role=ROLE.TEACHER,
        )
        from apps.teacher.models import Teacher

        Teacher.objects.create(user=user)
        self.client.force_authenticate(user=user)

        response = self.client.post(
            reverse("user-change-password"),
            {
                "old_password": "wrong-old",
                "new_password": "newpass12345",
                "new_password_confirm": "newpass12345",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["old_password"][0], "Eski parol noto'g'ri.")

    def test_change_password_fails_when_confirmation_does_not_match(self):
        user = User.objects.create_user(
            phone_number="+998904444444",
            password="oldpass123",
            role=ROLE.STUDENT,
        )
        Student.objects.create(
            user=user,
            full_name="Student User",
            phone_number="+998904444444",
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            reverse("user-change-password"),
            {
                "old_password": "oldpass123",
                "new_password": "newpass12345",
                "new_password_confirm": "newpass12346",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["new_password_confirm"][0],
            "Yangi parollar bir xil emas.",
        )
