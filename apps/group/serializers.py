
from rest_framework import serializers

from apps.group.models import Group

class GroupModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=Group
        fields=(
            'title',
            'course',
            'teacher',
            'room',
            'lessons_days_choice',
            'status',
            'start_lesson',
            'end_lesson',
            'total_student',
            'started_at',
            'closed_at',
        )


class GroupStatusModelSerializer(serializers.ModelSerializer):
    branch_id = serializers.IntegerField(required=False)
    class Meta:
        model=Group
        fields=(
            'status',
            'branch_id'
        )

class GroupDetailModelSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        source='course.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    branch = serializers.CharField(
        source='course.branch.name',
        read_only=True
    )

    class Meta:
        model = Group
        fields = (
            'title',
            'course',
            'lessons_days_choice',
            'start_lesson',
            'end_lesson',
            'room',
            'branch',
            'price'
        )