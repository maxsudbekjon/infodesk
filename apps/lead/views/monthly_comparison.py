from datetime import timedelta
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lead.models import Lead, Source


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
            name="start_date",
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
        OpenApiParameter(
            name="end_date",
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
    ],
)
class MonthlyLeadSourceComparisonAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        branch_id = request.query_params.get("branch_id")
        
        organizations = user.organization_set.all()
        if not organizations.exists():
            return Response(
                {"detail": "Only center owners can access this data"},
                status=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        base_queryset = Lead.objects.filter(
            center__in=organizations,
            course__branchs__id=branch_id
        ).distinct()
        # Custom vaqt — cache yo'q, to'g'ridan to'g'ri hisoblanadi
        if start_date and end_date:
            start_date = parse_datetime(start_date)
            end_date = parse_datetime(end_date)

            if not start_date or not end_date:
                return Response(
                    {"detail": "Invalid datetime format. Use ISO format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            current_qs = base_queryset.filter(
                created_at__gte=start_date, created_at__lte=end_date
            ).values("source").annotate(count=Count("id"))
            
            current_data = {item["source"]: item["count"] for item in current_qs}
            sources = Source.objects.filter(Q(center__in=organizations) | Q(is_static=True))
            result = {source.name: {"current": current_data.get(source.id, 0)} for source in sources}
            return Response(result)

        # Oylik qism — cache bilan
        org_ids = sorted(organizations.values_list("id", flat=True))
        cache_key = f"monthly_lead_source:orgs:{','.join(map(str, org_ids))}:branch:{branch_id}:{now.year}:{now.month}"
        
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        start_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_last_day = start_current_month - timedelta(days=1)
        start_previous_month = last_month_last_day.replace(day=1)

        current_qs = (
            base_queryset.filter(created_at__gte=start_current_month)
            .values("source")
            .annotate(count=Count("id"))
        )
        previous_qs = (
            base_queryset.filter(created_at__gte=start_previous_month, created_at__lt=start_current_month)
            .values("source")
            .annotate(count=Count("id"))
        )

        current_data = {item["source"]: item["count"] for item in current_qs}
        previous_data = {item["source"]: item["count"] for item in previous_qs}

        sources = Source.objects.filter(Q(center__in=organizations) | Q(is_static=True))

        result = {}
        for source in sources:
            current_count = current_data.get(source.id, 0)
            previous_count = previous_data.get(source.id, 0)
            if previous_count == 0:
                percentage = 100.0 if current_count > 0 else 0
            else:
                percentage = ((current_count - previous_count) / previous_count) * 100

            result[source.name] = {
                "current": current_count,
                "previous": previous_count,
                "percentage_change": round(percentage, 2),
            }

        cache.set(cache_key, result, 60 * 10)  # 30 daqiqa
        return Response(result)