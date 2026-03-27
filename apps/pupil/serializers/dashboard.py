from rest_framework import serializers


class StudentCourseSummaryItemSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    course_name = serializers.CharField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    coin = serializers.IntegerField()


class StudentCourseSummaryResponseSerializer(serializers.Serializer):
    courses = StudentCourseSummaryItemSerializer(many=True)


class StudentGroupListItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    course_id = serializers.IntegerField()
    course_name = serializers.CharField(allow_null=True, required=False)
    duration_months = serializers.IntegerField(allow_null=True, required=False)
    branch_id = serializers.IntegerField(allow_null=True, required=False)
    branch_name = serializers.CharField(allow_null=True, required=False)
    teacher_id = serializers.IntegerField(allow_null=True, required=False)
    teacher_name = serializers.CharField(allow_null=True, required=False)
    assistant_teacher_id = serializers.IntegerField(allow_null=True, required=False)
    assistant_teacher_name = serializers.CharField(allow_null=True, required=False)
    room = serializers.CharField(allow_null=True, required=False)
    lessons_days = serializers.ListField(child=serializers.CharField(), required=False)
    lessons_days_choice = serializers.CharField()
    status = serializers.CharField()
    start_lesson = serializers.TimeField()
    end_lesson = serializers.TimeField()
    total_student = serializers.IntegerField()
    started_at = serializers.DateField(allow_null=True, required=False)
    closed_at = serializers.DateField(allow_null=True, required=False)


class StudentGroupListResponseSerializer(serializers.Serializer):
    groups = StudentGroupListItemSerializer(many=True)


class StudentTodayCoinItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    group_id = serializers.IntegerField()
    group_title = serializers.CharField(allow_null=True, required=False)
    course_id = serializers.IntegerField(allow_null=True, required=False)
    course_name = serializers.CharField(allow_null=True, required=False)
    score = serializers.IntegerField()
    reason = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()


class StudentTodayCoinResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_coin = serializers.IntegerField()
    coins = StudentTodayCoinItemSerializer(many=True)
