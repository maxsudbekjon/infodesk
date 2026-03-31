from decimal import Decimal

from django.core.exceptions import PermissionDenied
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.market.models import MarketOrder, Product
from apps.market.serializers import MarketOrderSerializer, ProductSerializer
from apps.user.profile_resolver import get_student_profile


def _get_student_or_403(user):
    student = get_student_profile(user)
    if not student:
        raise PermissionDenied("Bu endpoint faqat student account uchun.")
    return student


@extend_schema(
    tags=["Market"],
    parameters=[
        OpenApiParameter(
            name="affordable",
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Only return products the current student's remaining coin can afford.",
        ),
    ],
)
class MarketProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        student = _get_student_or_403(self.request.user)
        queryset = Product.objects.order_by("-created_at")

        affordable = str(self.request.query_params.get("affordable", "")).lower()
        if affordable in {"1", "true", "yes"}:
            queryset = queryset.filter(price__lte=Decimal(student.available_coin))

        return queryset


@extend_schema(tags=["Market"])
class MarketOrderCreateAPIView(generics.CreateAPIView):
    serializer_class = MarketOrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = MarketOrder.objects.select_related("student", "product")

    def perform_create(self, serializer):
        _get_student_or_403(self.request.user)
        serializer.save()


@extend_schema(tags=["Market"])
class MarketOrderMeAPIView(generics.ListAPIView):
    serializer_class = MarketOrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        student = _get_student_or_403(self.request.user)
        return MarketOrder.objects.filter(student=student).select_related("student", "product").order_by("-created_at")
