from django.db import OperationalError, ProgrammingError
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
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
        display_name = user.display_name

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
        refresh["full_name"] = display_name
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
                "full_name": display_name,
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


class UserPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        old_password = attrs.get("old_password")
        new_password = attrs.get("new_password")
        new_password_confirm = attrs.get("new_password_confirm")

        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "Foydalanuvchi topilmadi."})

        if not user.check_password(old_password):
            raise serializers.ValidationError({"old_password": "Eski parol noto'g'ri."})

        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {"new_password_confirm": "Yangi parollar bir xil emas."}
            )

        if old_password == new_password:
            raise serializers.ValidationError(
                {"new_password": "Yangi parol eski parol bilan bir xil bo'lmasligi kerak."}
            )

        validate_password(new_password, user=user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class UserPasswordChangeResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
