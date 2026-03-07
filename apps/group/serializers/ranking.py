from rest_framework import serializers


class GroupRankingListSerializer(serializers.Serializer):
    rating = serializers.IntegerField()
    student = serializers.IntegerField()
    full_name = serializers.CharField()
    total_grade = serializers.DecimalField(max_digits=12, decimal_places=2)
    comment = serializers.CharField(allow_null=True)
