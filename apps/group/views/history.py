from rest_framework import generics

from apps.group.models.history import GroupHistory
from apps.group.serializers.history import (
    GroupHistoryCreateSerializer,
    GroupHistoryListSerializer,
)


class GroupHistoryCreateAPIView(generics.CreateAPIView):
    queryset = GroupHistory.objects.all()
    serializer_class = GroupHistoryCreateSerializer


class GroupHistoryListAPIView(generics.ListAPIView):
    serializer_class = GroupHistoryListSerializer

    def get_queryset(self):
        group_id = self.kwargs.get("id")
        return GroupHistory.objects.filter(group_id=group_id).order_by("-created_at")
