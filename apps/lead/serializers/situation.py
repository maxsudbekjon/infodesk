from rest_framework import serializers

from apps.lead.models import Situation


class SituationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Situation
        fields = ("organization", "title")
