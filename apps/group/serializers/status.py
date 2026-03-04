from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.group.models import Group
from apps.settings.models import Branch


class GroupStatusModelSerializer(serializers.ModelSerializer):
    branch_id = serializers.IntegerField(required=False)

    class Meta:
        model = Group
        fields = ("status", "branch_id")

    def validate(self, attrs):
        branch_id = attrs.get("branch_id")
        instance = getattr(self, "instance", None)

        if branch_id is not None:
            try:
                branch = Branch.objects.get(id=branch_id)
            except Branch.DoesNotExist:
                raise ValidationError({"branch_id": "Branch topilmadi."})

            if not instance:
                raise ValidationError({"branch_id": "Group topilmadi."})

            if not branch.courses.filter(id=instance.course_id).exists():
                raise ValidationError(
                    {"branch_id": "Ushbu branchda guruhga biriktirilgan kurs mavjud emas. Ko'chirish mumkin emas."}
                )

            attrs["branch_obj"] = branch

        return attrs

    def update(self, instance, validated_data):
        branch_obj = validated_data.pop("branch_obj", None)
        status = validated_data.get("status")

        if status is not None:
            instance.status = status

        if branch_obj:
            instance.branch = branch_obj

        instance.save()
        return instance
