from rest_framework import serializers


class StudentCourseSummaryItemSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    course_name = serializers.CharField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    coin = serializers.IntegerField()


class StudentCourseSummaryResponseSerializer(serializers.Serializer):
    courses = StudentCourseSummaryItemSerializer(many=True)
