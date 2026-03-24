from django.db import OperationalError, ProgrammingError
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.user.choices import ROLE
from apps.user.profile_resolver import find_student_by_phone_number, get_teacher_profile, get_student_profile


class UserLoginSerializer(TokenObtainPairSerializer):
    username_field = "phone_number"

    default_error_messages = {
        "no_active_account": "Telefon raqam yoki parol noto'g'ri.",
    }

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            phone_number=phone_number,
            password=password,
        )
        if not user:
            raise AuthenticationFailed(self.error_messages["no_active_account"])

        if not user.is_active:
            raise AuthenticationFailed("Bu account faol emas.")

        self.user = user
        student = self._resolve_student_profile(user)
        teacher = get_teacher_profile(user)

        if teacher:
            role = ROLE.TEACHER
        elif student:
            role = ROLE.STUDENT
        else:
            raise AuthenticationFailed(
                "Faqat teacher yoki student account tizimga kira oladi."
            )

        refresh = self.get_token(user)
        refresh["role"] = role
        refresh["full_name"] = user.full_name or ""
        refresh["phone_number"] = user.phone_number

        profile = {
            "teacher_id": teacher.id if teacher else None,
            "student_id": student.id if student else None,
        }
        refresh["teacher_id"] = profile["teacher_id"]
        refresh["student_id"] = profile["student_id"]

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "phone_number": user.phone_number,
                "role": role,
                **profile,
            },
        }

    def _resolve_student_profile(self, user):
        student = get_student_profile(user)
        if not student:
            return None

        if getattr(student, "user_id", None) == user.id:
            return student

        student.user = user
        try:
            student.save(update_fields=["user"])
        except (OperationalError, ProgrammingError):
            # Migration hali qo'llanmagan bo'lsa ham login ishlashda davom etadi.
            return find_student_by_phone_number(user.phone_number)

        return student
