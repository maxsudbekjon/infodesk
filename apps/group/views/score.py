from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.group.models.score import GroupScore
from apps.group.serializers.score import GroupScoreCreateSerializer

@extend_schema(tags=['Group'])
class GroupScoreCreateAPIView(generics.CreateAPIView):
    queryset = GroupScore.objects.all()
    serializer_class = GroupScoreCreateSerializer
