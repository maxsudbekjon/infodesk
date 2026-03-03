from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.group.models import Group


class GroupModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = (
            "title",
            "course",
            "branch",
            "teacher",
            "room",
            "lessons_days_choice",
            "status",
            "start_lesson",
            "end_lesson",
            "total_student",
            "started_at",
            "closed_at",
        )

    def validate_course(self, course):
        request = self.context.get("request")
        if not request:
            return course
        organizations = request.user.organization_set.all()
        if not organizations.exists():
            raise ValidationError("Organization topilmadi.")
        if course and course.center_id not in organizations.values_list("id", flat=True):
            raise ValidationError(
                "Faqat o'zingizga tegishli organizationdagi kursga guruh qo'sha olasiz."
            )
        return course
