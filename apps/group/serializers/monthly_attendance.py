from rest_framework import serializers


class MonthlyAttendanceCellSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True, required=False)
    day = serializers.IntegerField()
    is_present = serializers.BooleanField(allow_null=True)


class MonthlyAttendanceStudentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField(allow_null=True, required=False)
    image = serializers.URLField(allow_null=True, required=False)
    coin = serializers.IntegerField()
    used_coin = serializers.IntegerField()
    attendance_days = MonthlyAttendanceCellSerializer(many=True)


class GroupMonthlyAttendanceResponseSerializer(serializers.Serializer):
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    days = serializers.ListField(child=serializers.IntegerField())
    students = MonthlyAttendanceStudentSerializer(many=True)
