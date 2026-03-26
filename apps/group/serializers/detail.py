from rest_framework import serializers

from apps.group.models import Group
from apps.group.utils import build_student_image_url, get_group_students
from apps.pupil.models.student import Student


class GroupDetailModelSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        source="course.price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    branch = serializers.CharField(
        source="branch.name",
        read_only=True,
    )

    class Meta:
        model = Group
        fields = (
            "title",
            "course",
            "lessons_days_choice",
            "start_lesson",
            "end_lesson",
            "room",
            "branch",
            "price",
        )


class StudentModelSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model=Student
        fields=('id','full_name','phone_number','status','image')

    def get_image(self, obj):
        request = self.context.get("request")
        return build_student_image_url(obj, request=request)



class GroupStudentModelSerializer(serializers.ModelSerializer):
    students = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('id', 'students')

    def get_students(self, obj):
        return StudentModelSerializer(
            get_group_students(obj),
            many=True,
            context=self.context,
        ).data
