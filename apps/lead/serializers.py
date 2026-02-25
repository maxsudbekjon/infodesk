from rest_framework import serializers

from apps.lead.models import Lead
from apps.user.models import User

class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fileds=(
            'first_name',
            'last_name',
            'birth_day',
            'phone_number',
        )

class LeadModelSerializer(serializers.ModelSerializer):
    user=UserModelSerializer(many=True)
    class Meta:
        model=Lead
        fileds=(
            'user',
            'operator',
            'situation',
            'source',
            'temperature',
            'comment',
            'created_at'
        )
