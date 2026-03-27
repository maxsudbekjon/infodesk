from django.utils import timezone
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
        group = attrs.get("group") or getattr(self.instance, "group", None)
        student = attrs.get("student") or getattr(self.instance, "student", None)
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

        if self.instance and timezone.localdate(self.instance.created_at) != timezone.localdate():
            raise serializers.ValidationError(
                {"detail": "Faqat bugungi coinni update qilish mumkin."}
            )

        return attrs


class GroupScoreUpdateSerializer(GroupScoreCreateSerializer):
    class Meta(GroupScoreCreateSerializer.Meta):
        fields = ("id", "group", "student", "student_name", "score", "reason", "created_at")
        read_only_fields = ("id", "group", "student", "student_name", "created_at")
