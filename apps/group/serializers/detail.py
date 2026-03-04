from rest_framework import serializers

from apps.group.models import Group


class GroupDetailModelSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        source="course.price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    branch = serializers.CharField(
        source="room.branch.name",
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
