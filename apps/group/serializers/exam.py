from rest_framework import serializers

from apps.group.models.exam import Exam


class ExamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ("group", "title", "date", "pass_score", "max_score", "note", "extra_data")


class ExamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ("id", "group", "title", "date", "pass_score", "max_score", "note", "extra_data")
