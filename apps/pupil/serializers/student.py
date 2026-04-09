from django.db import transaction
from rest_framework import serializers
from apps.lead.models.situation import Situation
from apps.pupil.choices import STUDENT_STATUS, TRANSFER_REASON
from apps.pupil.models.student import Student, StudentTransfer
from apps.pupil.models.note import StudentNote






class StudentChangeGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudentTransfer
        fields = (
            "student",
            "to_group",
            "to_branch",
            "reason",
            "reason_choice",
            "is_apply_discount",
            "is_debt",
            "discount_amount",
            "discount_type",
            "specific_month",
            "from_group",
            "from_branch",
        )
        read_only_fields = ("from_group", "from_branch")

    def validate(self, attrs):
        student = attrs.get("student")
        to_group = attrs.get("to_group")

        if not student:
            raise serializers.ValidationError("student kiritilishi kerak")

        if not to_group:
            raise serializers.ValidationError("to_group kiritilishi kerak")

        # Student o‘z guruhiga transfer qilinmasligi
        if student.group and student.group == to_group:
            raise serializers.ValidationError(
                "Student allaqachon shu guruhda"
            )

        is_discount = attrs.get("is_apply_discount")

        discount_amount = attrs.get("discount_amount")
        discount_type = attrs.get("discount_type")
        specific_month = attrs.get("specific_month")

        # Discount ishlatilmasa boshqa fieldlar bo'sh bo'lishi kerak
        if not is_discount:
            if discount_amount is not None or discount_type or specific_month:
                raise serializers.ValidationError(
                    "Discount qo'llanmasa discount fieldlari kiritilmasligi kerak"
                )

        # Discount ishlatilsa majburiy fieldlar
        if is_discount:
            if discount_amount is None:
                raise serializers.ValidationError(
                    "discount_amount majburiy"
                )

            if not discount_type:
                raise serializers.ValidationError(
                    "discount_type majburiy"
                )

            if discount_type == "SPECIFIC_MONTH":
                if not specific_month or specific_month <= 0:
                    raise serializers.ValidationError(
                        "specific_month 0 dan katta bo'lishi kerak"
                    )

        return attrs

    def create(self, validated_data):
        student = validated_data["student"]

        # eski group va branch avtomatik olinadi
        validated_data["from_group"] = student.group
        validated_data["from_branch"] = (
            student.group.branch if student.group else None
        )

        transfer = StudentTransfer.objects.create(**validated_data)

        return transfer
    


class StudentReturnToLeadSerializer(serializers.Serializer):
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.select_related("lead", "center"),
        source="student",
        write_only=True,
    )
    situation_id = serializers.PrimaryKeyRelatedField(
        queryset=Situation.objects.all(),
        source="situation",
        write_only=True,
    )

    student = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    lead = serializers.IntegerField(read_only=True)
    situation = serializers.IntegerField(read_only=True)

    def validate(self, attrs):
        student = attrs.get("student")
        situation = attrs.get("situation")

        if not student:
            raise serializers.ValidationError("student kiritilishi kerak")

        if not student.lead:
            raise serializers.ValidationError("Studentda lead mavjud emas")

        if situation and situation.organization and student.lead.center:
            if situation.organization != student.lead.center:
                raise serializers.ValidationError("Bu situation bu centerga tegishli emas.")

        return attrs

    def create(self, validated_data):
        student = validated_data["student"]
        situation = validated_data["situation"]
        lead = student.lead

        with transaction.atomic():
            lead.situation = situation
            lead.save(update_fields=["situation_id"])

            student.status = STUDENT_STATUS.LEAD
            student.save(update_fields=["status"])

        return student

    def to_representation(self, instance):
        lead = instance.lead
        return {
            "student": instance.id,
            "status": instance.status,
            "lead": lead.id if lead else None,
            "situation": lead.situation_id if lead else None,
        }


class StudentRemoveFromGroupSerializer(serializers.Serializer):
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.select_related("group"),
        source="student",
        write_only=True,
    )
    reason_choice = serializers.ChoiceField(choices=TRANSFER_REASON.choices)
    reason = serializers.CharField()

    student = serializers.IntegerField(read_only=True)
    from_group = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)

    def validate(self, attrs):
        student = attrs.get("student")

        if not student:
            raise serializers.ValidationError("student kiritilishi kerak")

        if not student.group and not student.groups.exists():
            raise serializers.ValidationError("Student guruhga biriktirilmagan")

        return attrs

    def create(self, validated_data):
        student = validated_data["student"]
        reason = validated_data["reason"]
        reason_choice = validated_data["reason_choice"]
        from_group_id = student.group_id

        with transaction.atomic():
            StudentTransfer.objects.create(
                student=student,
                from_group=student.group,
                from_branch=student.group.branch if student.group else None,
                to_group=None,
                to_branch=None,
                reason=reason,
                reason_choice=reason_choice,
                is_apply_discount=False,
                is_debt=False,
            )

            if student.group_id:
                student.group = None
                student.save(update_fields=["group_id"])

            # M2M dagi barcha bog'lanishlarni ham tozalaymiz
            student.groups.clear()

        self._from_group_id = from_group_id
        return student

    def to_representation(self, instance):
        return {
            "student": instance.id,
            "from_group": getattr(self, "_from_group_id", None),
            "status": instance.status,
        }


class StudentNoteCreateSerializer(serializers.ModelSerializer):
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        source="student",
        write_only=True,
    )

    class Meta:
        model = StudentNote
        fields = ("student_id", "text", "date")
        read_only_fields = ("date",)

    def create(self, validated_data):
        request = self.context.get("request")
        operator = getattr(getattr(request, "user", None), "operator", None)
        return StudentNote.objects.create(operator=operator, **validated_data)


class StudentNoteListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentNote
        fields = ("id", "student", "student_name", "text", "date", "author_name")

    def get_author_name(self, obj):
        operator_user = getattr(obj.operator, "user", None)
        if operator_user:
            return f"{operator_user.first_name} {operator_user.last_name}".strip()
        return None
