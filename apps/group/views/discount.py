from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.group.models.discount import GroupDiscount
from apps.group.serializers.discount import (
    GroupDiscountCreateSerializer,
    GroupDiscountListSerializer,
)

@extend_schema(tags=['Group'])
class GroupDiscountCreateAPIView(generics.CreateAPIView):
    queryset = GroupDiscount.objects.all()
    serializer_class = GroupDiscountCreateSerializer

@extend_schema(tags=['Group'])
class GroupDiscountListAPIView(generics.ListAPIView):
    serializer_class = GroupDiscountListSerializer

    def get_queryset(self):
        group_id = self.kwargs.get("id")
        return (
            GroupDiscount.objects.filter(group_id=group_id)
            .select_related("student")
            .order_by("-created_at")
        )
