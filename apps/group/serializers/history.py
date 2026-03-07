from rest_framework import serializers

from apps.group.models.history import GroupHistory


class GroupHistoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupHistory
        fields = (
            "group",
            "title",
            "old_value",
            "new_value",
            "author_name",
            "extra_data",
            "created_at",
        )
        read_only_fields = ("created_at",)


class GroupHistoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupHistory
        fields = (
            "id",
            "group",
            "title",
            "old_value",
            "new_value",
            "author_name",
            "created_at",
            "extra_data",
        )
