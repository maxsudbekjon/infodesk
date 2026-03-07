from rest_framework import serializers

from apps.group.choices import GROUP_STATUS
from apps.group.models.freeze import GroupFreeze


class GroupFreezeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupFreeze
        fields = ("group", "reason", "start_date", "end_date", "created_at")
        read_only_fields = ("created_at",)

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("end_date start_date dan oldin bo'lishi mumkin emas.")

        return attrs

    def create(self, validated_data):
        group = validated_data["group"]
        freeze = GroupFreeze.objects.create(**validated_data)
        if group.status != GROUP_STATUS.FROZEN:
            group.status = GROUP_STATUS.FROZEN
            group.save(update_fields=["status"])
        return freeze
