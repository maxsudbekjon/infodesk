from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from apps.group.models import Group
from apps.group.serializers import GroupDetailModelSerializer
from apps.group.serializers.detail import GroupStudentModelSerializer


@extend_schema(tags=['Group'])
class GroupDetailAPIView(generics.RetrieveAPIView):
    serializer_class = GroupDetailModelSerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        organizations = user.organization.all()
        if not organizations.exists():
            return Group.objects.none()
        return Group.objects.select_related("room", "course", "branch").filter(
            branch__organization__in=organizations
        )


@extend_schema(tags=['Group'])
class GroupStudentAPIView(generics.RetrieveAPIView):
    queryset=Group.objects.all()
    serializer_class=GroupStudentModelSerializer
    lookup_field='id'

