
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.group.models import Group
from apps.settings.models import Branch

class GroupModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=Group
        fields=(
            'title',
            'course',
            'branch',
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

    def validate_course(self, course):
        request = self.context.get('request')
        if not request:
            return course
        organizations = request.user.organization_set.all()
        if not organizations.exists():
            raise ValidationError("Organization topilmadi.")
        if course and course.center_id not in organizations.values_list('id', flat=True):
            raise ValidationError("Faqat o'zingizga tegishli organizationdagi kursga guruh qo'sha olasiz.")
        return course


class GroupStatusModelSerializer(serializers.ModelSerializer):
    branch_id = serializers.IntegerField(required=False)
    class Meta:
        model=Group
        fields=(
            'status',
            'branch_id'
        )

    def validate(self, attrs):
        branch_id = attrs.get('branch_id')
        instance = getattr(self, 'instance', None)

        if branch_id is not None:
            try:
                branch = Branch.objects.get(id=branch_id)
            except Branch.DoesNotExist:
                raise ValidationError({'branch_id': "Branch topilmadi."})

            if not instance:
                raise ValidationError({'branch_id': "Group topilmadi."})

            if not branch.courses.filter(id=instance.course_id).exists():
                raise ValidationError({'branch_id': "Ushbu branchda guruhga biriktirilgan kurs mavjud emas. Ko'chirish mumkin emas."})

            attrs['branch_obj'] = branch

        return attrs

    def update(self, instance, validated_data):
        branch_obj = validated_data.pop('branch_obj', None)
        status = validated_data.get('status')

        if status is not None:
            instance.status = status

        if branch_obj:
            instance.branch = branch_obj

        instance.save()
        return instance

class GroupDetailModelSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        source='course.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    branch = serializers.CharField(
        source='room.branch.name',
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
