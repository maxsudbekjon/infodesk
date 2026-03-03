from rest_framework import generics

from apps.group.models import Group
from apps.group.serializers import GroupStatusModelSerializer


class GroupStatusUpdateAPIView(generics.UpdateAPIView):
    serializer_class = GroupStatusModelSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Group.objects.all()
