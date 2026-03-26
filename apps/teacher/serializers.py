import calendar
import re

from django.db.models import Count, Q
from django.db import transaction
from django.contrib.auth import get_user_model
from django.template.context_processors import request
from django.utils import timezone

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.teacher.models import Teacher, Specialty
from apps.group.models import Group, CourseTemplate
from apps.group.choices import GROUP_DAYS_CHOICES
from apps.group.utils import count_group_students
from apps.user.choices import ROLE

User = get_user_model()


DAY_ALIASES = {
    "mon": "monday",
    "monday": "monday",
    "dushanba": "monday",
    "tue": "tuesday",
    "tuesday": "tuesday",
    "seshanba": "tuesday",
    "wed": "wednesday",
    "wednesday": "wednesday",
    "chorshanba": "wednesday",
    "thu": "thursday",
    "thursday": "thursday",
    "payshanba": "thursday",
    "fri": "friday",
    "friday": "friday",
    "juma": "friday",
    "sat": "saturday",
    "saturday": "saturday",
    "shanba": "saturday",
    "sun": "sunday",
    "sunday": "sunday",
    "yakshanba": "sunday",
}


def normalize_day_value(value):
    cleaned = re.sub(r"[^a-z]+", "", str(value).lower())
    return DAY_ALIASES.get(cleaned, cleaned)


def today_day_value():
    return normalize_day_value(calendar.day_name[timezone.localdate().weekday()])


class SimpleUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'phone_number', 'password')


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ('id', 'title')


class TeacherGroupSerializer(serializers.ModelSerializer):
    lessons_days = serializers.SerializerMethodField()
    room = serializers.CharField(source="room.name", read_only=True, allow_null=True)
    duration_months = serializers.IntegerField(source="course.duration_months", read_only=True)
    attendance_today = serializers.SerializerMethodField()
    total_student = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = (
           'id',
            'title',
            "lessons_days",
            "room",
            'start_lesson',
            'end_lesson',
            'duration_months',
            'total_student',
            'attendance_today',
        )

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_lessons_days(self, obj):
        return [day.day for day in sorted(obj.lessons_days.all(), key=lambda item: item.id or 0)]

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_attendance_today(self, obj):
        lessons_days = list(obj.lessons_days.all())
        if lessons_days:
            today_value = today_day_value()
            return any(normalize_day_value(day.day) == today_value for day in lessons_days)

        if obj.lessons_days_choice == GROUP_DAYS_CHOICES.EVERAY_DAY:
            return True

        current_day = timezone.localdate().day
        if obj.lessons_days_choice == GROUP_DAYS_CHOICES.ODD_DAYS:
            return current_day % 2 == 1
        if obj.lessons_days_choice == GROUP_DAYS_CHOICES.EVEN_DAYS:
            return current_day % 2 == 0
        return False

    @extend_schema_field(OpenApiTypes.INT)
    def get_total_student(self, obj):
        return count_group_students(obj)


class TeacherSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer()
    specialties = SpecialtySerializer(source='specialty', many=True, read_only=True)
    groups = TeacherGroupSerializer(source='main_groups', many=True, read_only=True)
    groups_count = serializers.IntegerField(read_only=True)
    students_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Teacher
        fields = (
            'id', 'user', 'image',
            'specialties', 'groups',
            'monthly_salary', 'kpi', 'monthly_per_lesson', 'monthly_per_student',
            'contract_date', 'percentage_share', 'lesson_fee', 'per_student_fee',
            'branch', 'is_archived',
            'created_at', 'updated_at', 'groups_count', 'students_count'
        )
        read_only_fields = ('created_at', 'updated_at', 'groups_count', 'students_count')


    def update(self, instance, validated_data):
        specialties = validated_data.pop('specialty', None)
        teacher = super().update(instance, validated_data)
        if specialties is not None:
            teacher.specialty.set(specialties)
        return teacher


class TeacherListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    phone = serializers.CharField(source='user.phone_number', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = (
            'id',
            'full_name',
            'phone',
            'image_url',
            'monthly_salary',
            'percentage_share',
            'branch_id',
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


class TeacherArchiveToggleResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    is_archived = serializers.BooleanField()


class TeacherDeleteResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class TeacherImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()

    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image size must be under 5MB.")
        return value


class TeacherCreateSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer()
    specialties = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Specialty.objects.all(),
        required=False
    )

    class Meta:
        model = Teacher
        fields = (
            'id', 'user',
            'specialties',
            'monthly_salary', 'kpi', 'monthly_per_lesson', 'monthly_per_student',
            'contract_date', 'percentage_share', 'lesson_fee', 'per_student_fee',
            'branch', 'is_archived',
        )
        # read_only_fields = ('created_at', 'updated_at', 'courses_count', 'groups_count', 'students_count')

    def create(self, validated_data):
        request = self.context["request"]
        user_data = validated_data.pop('user')
        speciaties = validated_data.pop('specialties')
        branch = validated_data.get('branch')

        if not user_data.get("password"):
            raise serializers.ValidationError({"user": {"password": "Password majburiy."}})

        if branch and branch.organization.owner != request.user:
            raise serializers.ValidationError("You do not have permission to assign this branch.")

        with transaction.atomic():
            user_data["role"] = ROLE.TEACHER
            user = User.objects.create_user(**user_data)
            teacher = Teacher.objects.create(
                user=user,
                **validated_data
            )
            teacher.specialty.set(speciaties)

        return teacher


class TeacherUpdateSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    specialty = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Teacher
        fields = (
            'id', 'user',
            'specialty',
            'monthly_salary', 'kpi', 'monthly_per_lesson', 'monthly_per_student',
            'contract_date', 'percentage_share', 'lesson_fee', 'per_student_fee',
            'branch', 'is_archived',
        )
