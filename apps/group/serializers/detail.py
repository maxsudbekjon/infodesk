from rest_framework import serializers

from apps.group.models import Group
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
    class Meta:
        model=Student
        fields=('id','full_name','phone_number','status')



class GroupStudentModelSerializer(serializers.ModelSerializer):
    students=StudentModelSerializer(many=True)
    class Meta:
        model=Group
        fields=('id','students')
    
