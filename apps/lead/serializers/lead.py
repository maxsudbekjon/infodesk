from rest_framework import serializers

from apps.lead.models import Lead
from apps.lead.services import assign_for_new_lead
from apps.lead.tasks import process_sold_lead


class LeadModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = (
            "full_name",
            "phone_number",
            "course",
            "operator",
            "situation",
            "source",
            "temperature",
            "comment",
            "prefer_time",
            "days_choice",
        )

    def create(self, validated_data):
        lead = Lead.objects.create(**validated_data)
        return assign_for_new_lead(lead)


class LeadListModelSerializer(serializers.ModelSerializer):
    operator_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = (
            "full_name",
            "phone_number",
            "created_at",
            "operator_full_name",
            "situation",
        )

    def get_operator_full_name(self, obj):
        operator_user = getattr(obj.operator, "user", None)
        if operator_user:
            return f"{operator_user.first_name} {operator_user.last_name}"
        return None


class LeadAddGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ("group",)

class LeadSituationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ["situation"]
    def validate_situation(self, situation):
        lead = self.instance
        if situation and situation.organization and situation.organization != lead.center:
            raise serializers.ValidationError("Bu situation bu centerga tegishli emas.")
        return situation

    def update(self, instance, validated_data):
        situation = validated_data.get("situation")
        instance.situation = situation
        instance.save(update_fields=["situation"])

        if (
            situation
            and situation.is_static
            and situation.title.lower() == "sotildi"
        ):
            process_sold_lead.delay(instance.id)  # ← API ni kutmaydi, background da ishlaydi

        return instance