from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.group.models.note import GroupNote
from apps.group.serializers.note import (
    GroupNoteCreateSerializer,
    GroupNoteListSerializer,
)

@extend_schema(tags=['Group'])
class GroupNoteCreateAPIView(generics.CreateAPIView):
    queryset = GroupNote.objects.all()
    serializer_class = GroupNoteCreateSerializer

@extend_schema(tags=['Group'])
class GroupNoteListAPIView(generics.ListAPIView):
    serializer_class = GroupNoteListSerializer

    def get_queryset(self):
        group_id = self.kwargs.get("id")
        return GroupNote.objects.filter(group_id=group_id).order_by("-date")
