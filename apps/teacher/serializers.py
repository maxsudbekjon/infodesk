from django.db.models import Count, Q
from django.db import transaction
from django.contrib.auth import get_user_model
from django.template.context_processors import request

from rest_framework import serializers

from apps.teacher.models import Teacher, Specialty
from apps.group.models import Group, CourseTemplate
from apps.user.choices import ROLE

User = get_user_model()


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
    course = serializers.CharField(source='course.name', read_only=True)
    room = serializers.CharField(source='room.name', read_only=True)

    class Meta:
        model = Group
        fields = (
            'id',
            'title',
            "course",
            'room',
            'status',
            "lessons_days_choice",
            'start_lesson',
            'end_lesson',
            'total_student',
        )


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

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


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
