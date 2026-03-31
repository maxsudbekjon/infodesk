from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import Coalesce
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

        score_value = attrs.get("score", getattr(self.instance, "score", 0))
        if score_value < 0:
            raise serializers.ValidationError(
                {"score": "Coin manfiy bo'lishi mumkin emas."}
            )

        score_date = timezone.localdate(self.instance.created_at) if self.instance else timezone.localdate()
        today_total_qs = GroupScore.objects.filter(
            student=student,
            created_at__date=score_date,
        )
        if self.instance:
            today_total_qs = today_total_qs.exclude(pk=self.instance.pk)

        today_total = today_total_qs.aggregate(total_score=Coalesce(Sum("score"), 0))["total_score"]
        if today_total + score_value > 20:
            raise serializers.ValidationError(
                {"score": "Bir studentga bir kunda 20 tadan ko'p coin qo'yib bo'lmaydi."}
            )

        return attrs


class GroupScoreUpdateSerializer(GroupScoreCreateSerializer):
    class Meta(GroupScoreCreateSerializer.Meta):
        fields = ("id", "group", "student", "student_name", "score", "reason", "created_at")
        read_only_fields = ("id", "group", "student", "student_name", "created_at")
