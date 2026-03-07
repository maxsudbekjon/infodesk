from rest_framework import serializers

from apps.group.models.note import GroupNote


class GroupNoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupNote
        fields = ("group", "author_name", "text", "date")
        read_only_fields = ("date",)


class GroupNoteListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupNote
        fields = ("id", "group", "author_name", "text", "date")
