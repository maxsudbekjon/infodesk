from rest_framework import serializers

from apps.group.models.discount import GroupDiscount


class GroupDiscountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDiscount
        fields = (
            "group",
            "student",
            "remaining_months",
            "price",
            "author_name",
            "note",
            "extra_data",
            "created_at",
        )
        read_only_fields = ("created_at",)


class GroupDiscountListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = GroupDiscount
        fields = (
            "id",
            "group",
            "student",
            "student_name",
            "remaining_months",
            "created_at",
            "price",
            "author_name",
            "note",
            "extra_data",
        )
