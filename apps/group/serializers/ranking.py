from rest_framework import serializers


class GroupRankingListSerializer(serializers.Serializer):
    rating = serializers.IntegerField()
    student = serializers.IntegerField()
    full_name = serializers.CharField(allow_null=True, required=False)
    total_grade = serializers.DecimalField(max_digits=12, decimal_places=2)
    image = serializers.URLField(allow_null=True, required=False)
    comment = serializers.CharField(allow_null=True, required=False)
