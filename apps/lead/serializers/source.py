from rest_framework import serializers

from apps.lead.models import Source


class SourceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = (
            "name",
            "icon",
            "center",
        )
