
from rest_framework import serializers

from apps.group.models import Group, GroupNote


class GroupModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=Group
        fields=(
            'title',
            'course',
            'teacher',
            'room',
            'lessons_days_choice',
            'status',
            'start_lesson',
            'end_lesson',
            'total_student',
            'started_at',
            'closed_at',
        )


class GroupStatusModelSerializer(serializers.ModelSerializer):
    branch_id = serializers.IntegerField(required=False)
    class Meta:
        model=Group
        fields=(
            'status',
            'branch_id'
        )

class GroupDetailModelSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        source='course.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    branch = serializers.CharField(
        source='course.branch.name',
        read_only=True
    )

    class Meta:
        model = Group
        fields = (
            'title',
            'course',
            'lessons_days_choice',
            'start_lesson',
            'end_lesson',
            'room',
            'branch',
            'price'
        )



class GroupNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField(read_only=True)
    is_owner = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GroupNote
        fields = ['id', 'group', 'author', 'author_name', 'text', 'created_at', 'is_owner']
        read_only_fields = ['author']

    def get_author_name(self, obj):
        if obj.author:
            return obj.author.get_full_name() or getattr(obj.author, 'phone_number', "Noma'lum")
        return "Noma'lum"

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.author == request.user
        return False