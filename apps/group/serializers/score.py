from rest_framework import serializers

from apps.group.models.score import GroupScore
from apps.group.permissions import get_teacher_profile, user_can_access_group_as_student


class GroupScoreCreateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = GroupScore
        fields = ("id", "group", "student", "student_name", "score", "reason", "created_at")
        read_only_fields = ("created_at",)

    def validate(self, attrs):
        request = self.context.get("request")
        group = attrs.get("group")
        student = attrs.get("student")
        teacher = get_teacher_profile(getattr(request, "user", None))

        if not teacher:
            raise serializers.ValidationError(
                {"detail": "Siz teacher sifatida ro'yxatdan o'tmagansiz."}
            )

        if group.teacher_id != teacher.id and group.assistant_teacher_id != teacher.id:
            raise serializers.ValidationError(
                {"detail": "Siz bu guruhga coin qo'sha olmaysiz. Bu guruh sizga tegishli emas."}
            )

        if not user_can_access_group_as_student(group, student):
            raise serializers.ValidationError(
                {"detail": "Bu talaba shu guruhga tegishli emas."}
            )

        return attrs
