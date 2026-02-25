from rest_framework import serializers

from apps.lead.models import Lead
from apps.user.models import User

class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=(
            'first_name',
            'last_name',
            'birthday',
            'phone_number',
        )

class LeadModelSerializer(serializers.ModelSerializer):
    user=UserModelSerializer(many=True)
    class Meta:
        model=Lead
        fields=(
            'user',
            'operator',
            'situation',
            'source',
            'temperature',
            'comment',
            'prefer_time',
            'days_choice',
        )
