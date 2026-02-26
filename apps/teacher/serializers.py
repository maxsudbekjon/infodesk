from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Teacher, Specialty  # Branch if needed

User = get_user_model()

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'phone_number')

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ('id', 'title')

class TeacherSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='user', required=False, allow_null=True)
    specialty = serializers.PrimaryKeyRelatedField(queryset=Specialty.objects.all(), many=True, required=False)
    specialties = SpecialtySerializer(source='specialty', many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    courses_count = serializers.IntegerField(read_only=True)
    groups_count = serializers.IntegerField(read_only=True)
    students_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Teacher
        fields = (
            'id','user','user_id','image','image_url',
            'specialty','specialties',
            'monthly_salary','kpi','monthly_per_lesson','monthly_per_student',
            'birth_date','contract_date','percentage_share','lesson_fee','per_student_fee',
            'gender','branch','is_archived','registration_date',
            'courses_count','groups_count','students_count',
            'created_at','updated_at'
        )
        read_only_fields = ('created_at','updated_at','courses_count','groups_count','students_count')

    def get_image_url(self, obj) -> str | None:
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

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