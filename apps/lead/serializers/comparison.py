from rest_framework import serializers


class LeadSourceMonthlyComparisonSerializer(serializers.Serializer):
    source = serializers.CharField()
    current = serializers.IntegerField()
    previous = serializers.IntegerField()
    percentage_change = serializers.FloatField()
