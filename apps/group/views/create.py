from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.group.models import Group
from apps.group.serializers import GroupModelSerializer


class GroupCreateAPIView(generics.CreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupModelSerializer
    permission_classes = [IsAuthenticated]
