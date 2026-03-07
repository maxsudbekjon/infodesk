from rest_framework import serializers

from apps.group.models.grade import Grade


class GradeModelSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = Grade
        fields = ("id", "student", "student_name", "group", "date", "grade", "note")
