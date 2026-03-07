from rest_framework import generics

from apps.group.models.freeze import GroupFreeze
from apps.group.serializers.freeze import GroupFreezeCreateSerializer


class GroupFreezeCreateAPIView(generics.CreateAPIView):
    queryset = GroupFreeze.objects.all()
    serializer_class = GroupFreezeCreateSerializer
