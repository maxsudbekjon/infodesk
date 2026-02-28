from rest_framework import serializers
from django.db import transaction
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
            'phone_number2',
        )

class LeadModelSerializer(serializers.ModelSerializer):
    user = UserModelSerializer()  # many=True emas

    class Meta:
        model = Lead
        fields = (
            'user',
            'operator',
            'situation',
            'source',
            'temperature',
            'comment',
            'prefer_time',
            'days_choice',
        )

    

    def validate(self, attrs):
        user_data = attrs.get('user')

        if not user_data.get('phone_number'):
            raise serializers.ValidationError("Phone number majburiy.")

        return attrs

    def create(self, validated_data):
        user_data = validated_data.pop('user')

        with transaction.atomic():
            user, created = User.objects.get_or_create(
                phone_number=user_data['phone_number'],
                defaults=user_data
            )

            # agar user mavjud bo‘lsa va ma’lumot yangilanishi kerak bo‘lsa:
            if not created:
                for key, value in user_data.items():
                    setattr(user, key, value)
                user.save()

            lead = Lead.objects.create(user=user, **validated_data)

        return lead
    

class LeadListModelSerializer(serializers.ModelSerializer):
    first_name=serializers.CharField(source='user.first_name',read_only=True)
    last_name=serializers.CharField(source='user.last_name',read_only=True)
    phone_number=serializers.CharField(source='user.phone_number',read_only=True)
    operator_full_name = serializers.SerializerMethodField()
    class Meta:
        model=Lead
        fields=(
            'first_name',
            'last_name',
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