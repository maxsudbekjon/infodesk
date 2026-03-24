from rest_framework import serializers

from apps.group.models.grade import Grade
from apps.group.permissions import get_teacher_profile


class GradeModelSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = Grade
        fields = ("id", "student", "student_name", "group", "date", "grade", "note")

    def validate(self, attrs):
        request = self.context.get("request")
        group = attrs.get("group")
        student = attrs.get("student")
        date = attrs.get("date")

        teacher = get_teacher_profile(getattr(request, "user", None))
        if not teacher:
            raise serializers.ValidationError(
                {"detail": "Siz teacher sifatida ro'yxatdan o'tmagansiz."}
            )

        is_main_teacher = group.teacher == teacher
        is_assistant = group.assistant_teacher == teacher

        if not (is_main_teacher or is_assistant):
            raise serializers.ValidationError(
                {"detail": "Siz bu guruhga baho qo'sha olmaysiz. Bu guruh sizga tegishli emas."}
            )

        if not group.students.filter(id=student.id).exists():
            raise serializers.ValidationError(
                {"detail": "Bu talaba shu guruhga tegishli emas."}
            )

        queryset = Grade.objects.filter(student=student, group=group, date=date)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                {"detail": "Bu student uchun shu sana bo'yicha baho allaqachon mavjud."}
            )

        return attrs
