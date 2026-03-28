from collections import defaultdict

from drf_spectacular.utils import extend_schema_field
from django.utils import timezone
from rest_framework import serializers

from apps.group.models import Group
from apps.group.utils import build_student_image_url, get_group_students


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


class GroupStudentCardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField(allow_null=True, required=False)
    image = serializers.URLField(allow_null=True, required=False)
    coin = serializers.IntegerField()
    earned_coin = serializers.IntegerField()
    used_coin = serializers.IntegerField()
    today_coin = serializers.IntegerField()


class GroupStudentModelSerializer(serializers.ModelSerializer):
    students = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('id', 'students')

    @extend_schema_field(GroupStudentCardSerializer(many=True))
    def get_students(self, obj):
        students = get_group_students(obj)
        score_map = defaultdict(int)
        today_score_map = defaultdict(int)
        today = timezone.localdate()

        for score in obj.scores.all():
            score_map[score.student_id] += score.score
            if timezone.localdate(score.created_at) == today:
                today_score_map[score.student_id] += score.score

        ordered_students = sorted(
            students,
            key=lambda student: (
                -score_map.get(student.id, 0),
                (student.full_name or "").lower(),
                student.id,
            ),
        )

        payload = [
            {
                "id": student.id,
                "full_name": student.full_name,
                "image": build_student_image_url(student, request=self.context.get("request")),
                "coin": max(score_map.get(student.id, 0) - (student.used_coin or 0), 0),
                "earned_coin": score_map.get(student.id, 0),
                "used_coin": student.used_coin or 0,
                "today_coin": today_score_map.get(student.id, 0),
            }
            for student in ordered_students
        ]

        return GroupStudentCardSerializer(payload, many=True).data
