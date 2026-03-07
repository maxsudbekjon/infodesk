from rest_framework import serializers

from apps.group.models.score import GroupScore


class GroupScoreCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupScore
        fields = ("group", "student", "score", "reason", "created_at")
        read_only_fields = ("created_at",)
