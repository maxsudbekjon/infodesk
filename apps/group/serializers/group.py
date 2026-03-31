from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.group.models import Group
from apps.group.models.course import CourseTemplate
from apps.group.utils import count_group_students
from apps.teacher.models import Teacher
from apps.user.models.user import User

class UserModelSerializerForGroup(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=(
            'full_name',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["full_name"] = instance.display_name
        return data

class CourseTemplateModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=CourseTemplate
        fields=(
            'id',
            'name'
        )
class TeacherSerializerForGroup(serializers.ModelSerializer):
    user = UserModelSerializerForGroup(read_only=True)
    class Meta:
        model=Teacher
        fields=(
            'id',
            'user'
        )


class GroupModelSerializer(serializers.ModelSerializer):
    course = CourseTemplateModelSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        source="course",
        queryset=CourseTemplate.objects.all(),
        write_only=True,
    )
    teacher = TeacherSerializerForGroup(read_only=True)
    assistant_teacher = TeacherSerializerForGroup(read_only=True)
    total_student = serializers.SerializerMethodField()
    class Meta:
        model = Group
        fields = (
            "title",
            "course",
            "course_id",
            "branch",
            "teacher",
            'assistant_teacher',
            "room",
            "lessons_days_choice",
            "status",
            "start_lesson",
            "end_lesson",
            "total_student",
            "started_at",
            "closed_at",
        )

    def get_total_student(self, obj):
        return count_group_students(obj)

    def validate(self, attrs):
        course = attrs.get("course")
        request = self.context.get("request")
        if not request:
            return attrs
        organizations = request.user.organization.all()
        if not organizations.exists():
            raise ValidationError("Organization topilmadi.")
        if course and course.center_id not in organizations.values_list("id", flat=True):
            raise ValidationError(
                "Faqat o'zingizga tegishli organizationdagi kursga guruh qo'sha olasiz."
            )
        return attrs
