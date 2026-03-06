from apps.group.models.attendance import Attendance
from rest_framework import serializers


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
        group = attrs.get('group')
        student = attrs.get('student')

        # Request yuborgan user ning Teacher ob'ektini olish
        try:
            teacher = request.user.teachers  # OneToOneField → related_name='teachers'
        except Exception:
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
        # (Group modelida 'studnets' deb yozilgan — typo, lekin shunga mos ishlatamiz)
        if not group.students.filter(id=student.id).exists():
            raise serializers.ValidationError({
                'detail': 'Bu talaba shu guruhga tegishli emas.'
            })

        return attrs