from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.group.models import Group
from apps.group.serializers import GroupModelSerializer

@extend_schema(tags=['Group'])
class GroupCreateAPIView(generics.CreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupModelSerializer
    permission_classes = [IsAuthenticated]
