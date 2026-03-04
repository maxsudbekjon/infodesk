from rest_framework import serializers
from apps.group.models import GroupNote

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