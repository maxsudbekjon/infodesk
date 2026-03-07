from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from apps.group.models import Group


@extend_schema(tags=["Group"])
class GroupDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        organizations = user.organization_set.all()
        if not organizations.exists():
            return Group.objects.none()
        return Group.objects.filter(branch__organization__in=organizations)
