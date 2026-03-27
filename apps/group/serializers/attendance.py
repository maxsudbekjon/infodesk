from django.utils import timezone

from apps.group.models.attendance import Attendance
from rest_framework import serializers
from apps.group.permissions import get_teacher_profile, user_can_access_group_as_student


class AttendanceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=Attendance
        fields=(
            'group',
            'student',
            'date',
            'is_present',
            'note'
        )
    def validate(self, attrs):
        request = self.context.get('request')
        group = attrs.get('group') or getattr(self.instance, 'group', None)
        student = attrs.get('student') or getattr(self.instance, 'student', None)

        # Request yuborgan user ning Teacher ob'ektini olish
        teacher = get_teacher_profile(getattr(request, "user", None))
        if not teacher:
            raise serializers.ValidationError({
                'detail': 'Siz teacher sifatida ro\'yxatdan o\'tmagan siz.'
            })

        # 1. Shu guruhning teacher yoki assistant_teacher ekanligini tekshirish
        is_main_teacher = group.teacher == teacher
        is_assistant = group.assistant_teacher == teacher

        if not (is_main_teacher or is_assistant):
            raise serializers.ValidationError({
                'detail': 'Siz bu guruhga davomat qila olmaysiz. Bu guruh sizga tegishli emas.'
            })

        # 2. Student shu groupga tegishli ekanligini tekshirish
        if not user_can_access_group_as_student(group, student):
            raise serializers.ValidationError({
                'detail': 'Bu talaba shu guruhga tegishli emas.'
            })

        if self.instance and self.instance.date != timezone.localdate():
            raise serializers.ValidationError({
                'detail': 'Faqat bugungi davomatni update qilish mumkin.'
            })

        return attrs


class AttendanceUpdateSerializer(AttendanceModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = Attendance
        fields = (
            "id",
            "group",
            "student",
            "student_name",
            "date",
            "is_present",
            "note",
        )
        read_only_fields = ("id", "group", "student", "student_name", "date")


class GroupAttendanceModelSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name")

    class Meta:
        model = Attendance
        fields = (
            "id",
            "student",
            "student_name",
            "date",
            "is_present",
            "note",
        )
