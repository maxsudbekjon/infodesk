from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from apps.lead.models import Lead
from apps.lead.serializers import LeadListModelSerializer
from apps.lead.views.utils import LeadPagination, parse_bool
from apps.user.models import Operator


@extend_schema(
    tags=["Lead"],
    parameters=[
        OpenApiParameter(
            name="branch_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Branch ID for filtering leads",
        ),
        OpenApiParameter(
            name="is_active",
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
        OpenApiParameter(
            name="is_archived",
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
    ],
)
class LeadListAPIView(generics.ListAPIView):
    serializer_class = LeadListModelSerializer
    pagination_class = LeadPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        base_queryset = (
            Lead.objects.select_related("operator__user", "situation")
            .only(
                "created_at",
                "situation",
                "operator__user__first_name",
                "operator__user__last_name",
            )
            .order_by("-created_at")
        )

        organizations = user.organization_set.all()
        if organizations.exists():
            queryset = base_queryset.filter(center__in=organizations)
        else:
            try:
                operator = user.operator
            except Operator.DoesNotExist:
                operator = None
            if operator:
                queryset = base_queryset.filter(operator__user=user)
            else:
                return Lead.objects.none()

        is_active = self.request.query_params.get("is_active")
        is_archived = self.request.query_params.get("is_archived")
        branch_id = self.request.query_params.get("branch_id")

        if is_active is not None:
            queryset = queryset.filter(is_active=parse_bool(is_active))

        if is_archived is not None:
            queryset = queryset.filter(is_archived=parse_bool(is_archived))
        if branch_id:
            queryset = queryset.filter(course__branchs=branch_id)
        return queryset

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
