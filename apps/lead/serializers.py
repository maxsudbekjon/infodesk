from rest_framework import serializers
from django.db import transaction
from apps.lead.models import Lead, Source
from apps.lead.services import assign_for_new_lead
from apps.user.models import User



class LeadModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Lead
        fields = (
            'full_name',
            'phone_number',
            'course',
            'operator',
            'situation',
            'source',
            'temperature',
            'comment',
            'prefer_time',
            'days_choice',
        )

    def create(self, validated_data):
        lead = Lead.objects.create(**validated_data)
        return assign_for_new_lead(lead)
    

class LeadListModelSerializer(serializers.ModelSerializer):
    operator_full_name = serializers.SerializerMethodField()
    class Meta:
        model=Lead
        fields=(
            'full_name',
            'phone_number',
            'created_at',
            'operator_full_name',
            'situation'
        )
    def get_operator_full_name(self, obj):
        operator_user = getattr(obj.operator, 'user', None)
        if operator_user:
            return f"{operator_user.first_name} {operator_user.last_name}"
        return None



class LeadSourceMonthlyComparisonSerializer(serializers.Serializer):
    source = serializers.CharField()
    current = serializers.IntegerField()
    previous = serializers.IntegerField()
    percentage_change = serializers.FloatField()


class SourceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=Source
        fields=(
            'name',
            'icon',
            'center',
            'is_static'
        )


class LeadAddGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model=Lead 
        fields=('group',)
    