from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.group.models.freeze import GroupFreeze
from apps.group.serializers.freeze import GroupFreezeCreateSerializer

@extend_schema(tags=['Group'])
class GroupFreezeCreateAPIView(generics.CreateAPIView):
    queryset = GroupFreeze.objects.all()
    serializer_class = GroupFreezeCreateSerializer
