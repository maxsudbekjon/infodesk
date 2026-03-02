from django.db.models import Count, Q
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.teacher.models import Teacher, Specialty
from apps.group.models import Group, CourseTemplate

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'phone_number')


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ('id', 'title')

class TeacherGroupSerializer(serializers.ModelSerializer):
    # total_students = serializers.IntegerField(source='students_count', read_only=True)

    class Meta:
        model = Group
        fields = (
            'id',
            'title',
            'room',
            'status',
            'start_lesson',
            'end_lesson',
            'students_count',
        )


class TeacherCourseSerializer(serializers.ModelSerializer):
    groups = TeacherGroupSerializer(many=True, read_only=True)
    total_groups = serializers.IntegerField(read_only=True)
    active_groups = serializers.IntegerField(read_only=True)

    class Meta:
        model = CourseTemplate
        fields = (
            'id',
            'name',
            'duration_months',
            'groups',
            'total_groups',
            'active_groups',
        )

class TeacherSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='user',
                                                 required=False, allow_null=True)
    specialties = SpecialtySerializer(source='specialty', many=True, read_only=True)
    courses = serializers.SerializerMethodField()
    courses_count = serializers.IntegerField(read_only=True)
    groups_count = serializers.IntegerField(read_only=True)
    students_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Teacher
        fields = (
            'id', 'user', 'user_id', 'image',
            'specialties',
            'monthly_salary', 'kpi', 'monthly_per_lesson', 'monthly_per_student',
            'contract_date', 'percentage_share', 'lesson_fee', 'per_student_fee',
            'branch', 'is_archived',
            'created_at', 'updated_at', 'courses', 'courses_count', 'groups_count', 'students_count'
        )
        read_only_fields = ('created_at', 'updated_at', 'courses_count', 'groups_count', 'students_count')

    def get_courses(self, obj):
        courses = (
            obj.teacher_courses
            .prefetch_related('groups')
            .annotate(
                total_groups=Count('groups', distinct=True),
                active_groups=Count('groups',
                                    filter=Q(groups__status='active'),
                                    distinct=True)
            )
        )
        return TeacherCourseSerializer(courses, many=True).data

    def create(self, validated_data):
        # handle specialty m2m and user assignment
        specialties = validated_data.pop('specialty', [])
        teacher = super().create(validated_data)
        if specialties:
            teacher.specialty.set(specialties)
        return teacher

    def update(self, instance, validated_data):
        specialties = validated_data.pop('specialty', None)
        teacher = super().update(instance, validated_data)
        if specialties is not None:
            teacher.specialty.set(specialties)
        return teacher



class TeacherListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    phone = serializers.CharField(source='user.phone_number', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = (
            'id',
            'first_name',
            'last_name',
            'phone',
            'image_url',
            'monthly_salary',
            'percentage_share',
        )

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None


class TeacherImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
