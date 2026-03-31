import calendar
from datetime import date, time, timedelta

from django.contrib import admin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from drf_spectacular.generators import SchemaGenerator
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
        self.today = timezone.localdate()
        self.attendance_date = date(self.today.year, self.today.month, 20)

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

        self.student_attendance = Attendance.objects.create(
            group=self.group,
            student=self.student,
            date=self.attendance_date,
            is_present=True,
        )
        self.other_student_attendance = Attendance.objects.create(
            group=self.group,
            student=self.other_student,
            date=self.attendance_date,
            is_present=False,
        )
        Grade.objects.create(
            group=self.group,
            student=self.student,
            date=self.attendance_date,
            grade=5,
        )
        Grade.objects.create(
            group=self.group,
            student=self.other_student,
            date=self.attendance_date,
            grade=3,
        )
        self.student_score = GroupScore.objects.create(
            group=self.group,
            student=self.student,
            score=10,
            reason="Excellent",
        )
        self.other_student_score = GroupScore.objects.create(
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

    def test_teacher_can_create_attendance_without_is_present_and_it_defaults_to_none(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.post(
            reverse("attendance-create"),
            {
                "group": self.group.id,
                "student": self.student.id,
                "date": "2026-03-22",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        attendance = Attendance.objects.get(
            group=self.group,
            student=self.student,
            date="2026-03-22",
        )
        self.assertIsNone(attendance.is_present)

    def test_teacher_can_update_today_attendance(self):
        self.client.force_authenticate(user=self.teacher_user)
        attendance = Attendance.objects.create(
            group=self.group,
            student=self.student,
            date=self.today,
            is_present=False,
            note="Old note",
        )

        response = self.client.patch(
            reverse("attendance-update", kwargs={"id": attendance.id}),
            {
                "is_present": True,
                "note": "Updated note",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attendance.refresh_from_db()
        self.assertTrue(attendance.is_present)
        self.assertEqual(attendance.note, "Updated note")

    def test_teacher_cannot_update_old_attendance(self):
        self.client.force_authenticate(user=self.teacher_user)
        attendance = Attendance.objects.create(
            group=self.group,
            student=self.student,
            date=self.today - timedelta(days=1),
            is_present=False,
        )

        response = self.client.patch(
            reverse("attendance-update", kwargs={"id": attendance.id}),
            {"is_present": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0],
            "Faqat bugungi davomatni update qilish mumkin.",
        )

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

    def test_teacher_can_update_today_score(self):
        self.client.force_authenticate(user=self.teacher_user)
        score = GroupScore.objects.create(
            group=self.group,
            student=self.student,
            score=6,
            reason="Old reason",
        )

        response = self.client.patch(
            reverse("group-score-update", kwargs={"id": score.id}),
            {
                "score": 10,
                "reason": "Updated reason",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        score.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual(score.score, 10)
        self.assertEqual(score.reason, "Updated reason")
        self.assertEqual(self.student.total_coin, 20)

    def test_teacher_cannot_create_score_above_daily_limit(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.post(
            reverse("group-score-create"),
            {
                "group": self.group.id,
                "student": self.student.id,
                "score": 11,
                "reason": "Overflow",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["score"][0],
            "Bir studentga bir kunda 20 tadan ko'p coin qo'yib bo'lmaydi.",
        )

    def test_teacher_can_create_negative_score_and_reduce_balance(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.post(
            reverse("group-score-create"),
            {
                "group": self.group.id,
                "student": self.student.id,
                "score": -5,
                "reason": "Penalty",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.student.refresh_from_db()
        created_score = GroupScore.objects.get(pk=response.data["id"])
        self.assertEqual(created_score.score, -5)
        self.assertEqual(self.student.total_coin, 5)

    def test_teacher_cannot_bypass_daily_positive_limit_with_penalty(self):
        self.client.force_authenticate(user=self.teacher_user)
        GroupScore.objects.create(
            group=self.group,
            student=self.student,
            score=-10,
            reason="Penalty",
        )

        response = self.client.post(
            reverse("group-score-create"),
            {
                "group": self.group.id,
                "student": self.student.id,
                "score": 20,
                "reason": "Too much reward",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["score"][0],
            "Bir studentga bir kunda 20 tadan ko'p coin qo'yib bo'lmaydi.",
        )

    def test_teacher_cannot_update_old_score(self):
        self.client.force_authenticate(user=self.teacher_user)
        score = GroupScore.objects.create(
            group=self.group,
            student=self.student,
            score=6,
            reason="Old reason",
            created_at=timezone.now() - timedelta(days=1),
        )

        response = self.client.patch(
            reverse("group-score-update", kwargs={"id": score.id}),
            {"score": 12},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"][0],
            "Faqat bugungi coinni update qilish mumkin.",
        )

    def test_teacher_can_list_students_of_group_by_id(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.get(reverse("group-student", kwargs={"id": self.group.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.group.id)
        students = response.data["students"]
        self.assertEqual(len(students), 3)
        self.assertEqual(students[0]["id"], self.student.id)
        self.assertEqual(students[0]["full_name"], self.student.full_name)
        self.assertEqual(students[0]["coin"], 10)
        self.assertEqual(students[0]["earned_coin"], 10)
        self.assertEqual(students[0]["used_coin"], 0)
        self.assertEqual(students[0]["today_coin"], 10)
        self.assertEqual(students[0]["today_coin_id"], self.student_score.id)
        self.assertIsNotNone(students[0]["image"])
        self.assertIn("student-avatar", students[0]["image"])
        self.assertNotIn("rating", students[0])

        self.assertEqual(students[1]["id"], self.other_student.id)
        self.assertEqual(students[1]["coin"], 4)
        self.assertEqual(students[1]["earned_coin"], 4)
        self.assertEqual(students[1]["used_coin"], 0)
        self.assertEqual(students[1]["today_coin"], 4)
        self.assertEqual(students[1]["today_coin_id"], self.other_student_score.id)

        self.assertEqual(students[2]["id"], self.fk_only_student.id)
        self.assertEqual(students[2]["coin"], 0)
        self.assertEqual(students[2]["earned_coin"], 0)
        self.assertEqual(students[2]["used_coin"], 0)
        self.assertEqual(students[2]["today_coin"], 0)
        self.assertIsNone(students[2]["today_coin_id"])

    def test_group_student_list_shows_negative_today_coin_when_penalty_exists(self):
        self.client.force_authenticate(user=self.teacher_user)
        negative_score = GroupScore.objects.create(
            group=self.group,
            student=self.fk_only_student,
            score=-7,
            reason="Legacy penalty",
        )

        response = self.client.get(reverse("group-student", kwargs={"id": self.group.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        students = response.data["students"]
        third_student = next(item for item in students if item["id"] == self.fk_only_student.id)
        self.assertEqual(third_student["coin"], 0)
        self.assertEqual(third_student["earned_coin"], 0)
        self.assertEqual(third_student["today_coin"], -7)
        self.assertEqual(third_student["today_coin_id"], negative_score.id)

    def test_group_student_list_uses_student_balance_fields_for_totals(self):
        self.client.force_authenticate(user=self.teacher_user)
        self.fk_only_student.coin_offset = 150
        self.fk_only_student.total_coin = 75
        self.fk_only_student.save(update_fields=["coin_offset", "total_coin"])
        negative_score = GroupScore.objects.create(
            group=self.group,
            student=self.fk_only_student,
            score=-75,
            reason="Legacy penalty",
        )

        response = self.client.get(reverse("group-student", kwargs={"id": self.group.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        students = response.data["students"]
        third_student = next(item for item in students if item["id"] == self.fk_only_student.id)
        self.assertEqual(third_student["coin"], 75)
        self.assertEqual(third_student["earned_coin"], 75)
        self.assertEqual(third_student["today_coin"], -75)
        self.assertEqual(third_student["today_coin_id"], negative_score.id)

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

    def test_teacher_can_list_monthly_attendance_of_group(self):
        self.client.force_authenticate(user=self.teacher_user)

        response = self.client.get(reverse("group-monthly-attendance", kwargs={"id": self.group.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["month"], self.today.month)
        self.assertEqual(data["year"], self.today.year)
        self.assertEqual(len(data["days"]), calendar.monthrange(self.today.year, self.today.month)[1])
        self.assertIn(self.attendance_date.day, data["days"])
        self.assertSetEqual(
            {item["id"] for item in data["students"]},
            {self.student.id, self.other_student.id, self.fk_only_student.id},
        )
        student_row = next(item for item in data["students"] if item["id"] == self.student.id)
        self.assertEqual(student_row["coin"], 10)
        self.assertTrue(student_row["attendance_days"][self.attendance_date.day - 1]["is_present"])
        self.assertEqual(
            student_row["attendance_days"][self.attendance_date.day - 1]["id"],
            self.student_attendance.id,
        )

        other_row = next(item for item in data["students"] if item["id"] == self.other_student.id)
        self.assertEqual(other_row["coin"], 4)
        self.assertFalse(other_row["attendance_days"][self.attendance_date.day - 1]["is_present"])
        self.assertEqual(
            other_row["attendance_days"][self.attendance_date.day - 1]["id"],
            self.other_student_attendance.id,
        )

        fk_only_row = next(item for item in data["students"] if item["id"] == self.fk_only_student.id)
        self.assertEqual(fk_only_row["coin"], 0)
        self.assertTrue(all(day["is_present"] is None for day in fk_only_row["attendance_days"]))
        self.assertTrue(all(day["id"] is None for day in fk_only_row["attendance_days"]))

    def test_student_can_list_own_monthly_attendance_of_group(self):
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(reverse("group-monthly-attendance", kwargs={"id": self.group.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(len(data["students"]), 1)
        self.assertEqual(data["students"][0]["id"], self.student.id)
        self.assertEqual(data["students"][0]["coin"], 10)

    def test_monthly_attendance_can_filter_other_month(self):
        self.client.force_authenticate(user=self.teacher_user)

        first_of_month = self.today.replace(day=1)
        previous_month_date = first_of_month - timedelta(days=1)
        previous_month_attendance_date = previous_month_date.replace(day=20)

        Attendance.objects.create(
            group=self.group,
            student=self.student,
            date=previous_month_attendance_date,
            is_present=True,
        )

        response = self.client.get(
            reverse("group-monthly-attendance", kwargs={"id": self.group.id}),
            {
                "month": previous_month_attendance_date.month,
                "year": previous_month_attendance_date.year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["month"], previous_month_attendance_date.month)
        self.assertEqual(data["year"], previous_month_attendance_date.year)
        self.assertEqual(len(data["students"]), 3)

        student_row = next(item for item in data["students"] if item["id"] == self.student.id)
        self.assertEqual(student_row["coin"], 0)
        self.assertTrue(student_row["attendance_days"][previous_month_attendance_date.day - 1]["is_present"])
        self.assertEqual(data["days"][previous_month_attendance_date.day - 1], previous_month_attendance_date.day)

    def test_schema_includes_refresh_and_update_endpoints(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        self.assertIn("/api/token/refresh/", schema["paths"])
        self.assertIn("/apps/teachers/me/", schema["paths"])
        self.assertIn("/apps/pupil/me/", schema["paths"])
        self.assertIn("/apps/group/attendance/update/{id}", schema["paths"])
        self.assertIn("/apps/group/group-scores/update/{id}", schema["paths"])

    def test_grade_and_group_score_models_are_registered_in_admin(self):
        self.assertIn(Grade, admin.site._registry)
        self.assertIn(GroupScore, admin.site._registry)
