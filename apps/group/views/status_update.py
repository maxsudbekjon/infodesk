from rest_framework import generics
from drf_spectacular.utils import extend_schema
from apps.group.models import Group
from apps.group.serializers import GroupStatusModelSerializer


@extend_schema(tags=['Group'])
class GroupStatusUpdateAPIView(generics.UpdateAPIView):
    queryset=Group.objects.all()
    serializer_class = GroupStatusModelSerializer
    lookup_field = "id"
