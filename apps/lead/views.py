from rest_framework import generics
from apps.lead.models import Lead, Source
from apps.lead.serializers import LeadListModelSerializer, LeadModelSerializer, SourceModelSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import timedelta
from django.db.models import Q
from apps.user.models import Operator
from rest_framework import status
from django.utils.dateparse import parse_datetime




# LeadListAPIView uchun
def parse_bool(value):
    value = value.lower()
    if value in ['true', '1', 'yes']:
        return True
    if value in ['false', '0', 'no']:
        return False
    raise ValidationError("Boolean qiymat noto‘g‘ri.")



class LeadPagination(PageNumberPagination):
    page_size = 10


class LeadCreateAPIView(generics.CreateAPIView):
    queryset=Lead.objects.all()
    serializer_class=LeadModelSerializer
    permission_classes=[IsAuthenticated]



class LeadListAPIView(generics.ListAPIView):
    serializer_class = LeadListModelSerializer
    pagination_class = LeadPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        base_queryset = (
            Lead.objects
            .select_related(
                'operator__user',
                'situation',
            )
            .only(
                'created_at',
                'situation',
                'operator__user__first_name',
                'operator__user__last_name',
            )
            .order_by('-created_at')
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

        is_active = self.request.query_params.get('is_active')
        is_archived = self.request.query_params.get('is_archived')

        if is_active is not None:
            queryset = queryset.filter(is_active=parse_bool(is_active))

        if is_archived is not None:
            queryset = queryset.filter(is_archived=parse_bool(is_archived))

        return queryset

class MonthlyLeadSourceComparisonAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        organizations = user.organization_set.all()

        # 🔐 Faqat owner ko‘ra oladi
        if not organizations.exists():
            return Response(
                {"detail": "Only center owners can access this data"},
                status=status.HTTP_403_FORBIDDEN
            )

        now = timezone.now()

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        base_queryset = Lead.objects.filter(center__in=organizations)

        # ==============================
        # 📅 Custom date range
        # ==============================
        if start_date and end_date:
            start_date = parse_datetime(start_date)
            end_date = parse_datetime(end_date)

            if not start_date or not end_date:
                return Response(
                    {"detail": "Invalid datetime format. Use ISO format."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            current_qs = (
                base_queryset
                .filter(created_at__gte=start_date, created_at__lte=end_date)
                .values("source")
                .annotate(count=Count("id"))
            )

            current_data = {item["source"]: item["count"] for item in current_qs}

            result = {}

            for source, _ in LEAD_SOURCE.choices:
                result[source] = {
                    "current": current_data.get(source, 0),
                }

            return Response(result)

        # ==============================
        # 📅 Default: current vs previous month
        # ==============================
        start_current_month = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        last_month_last_day = start_current_month - timedelta(days=1)
        start_previous_month = last_month_last_day.replace(day=1)

        current_qs = (
            base_queryset
            .filter(created_at__gte=start_current_month)
            .values("source")
            .annotate(count=Count("id"))
        )

        previous_qs = (
            base_queryset
            .filter(
                created_at__gte=start_previous_month,
                created_at__lt=start_current_month
            )
            .values("source")
            .annotate(count=Count("id"))
        )

        current_data = {item["source"]: item["count"] for item in current_qs}
        previous_data = {item["source"]: item["count"] for item in previous_qs}

        result = {}

        for source, _ in LEAD_SOURCE.choices:
            current_count = current_data.get(source, 0)
            previous_count = previous_data.get(source, 0)

            if previous_count == 0:
                percentage = 100.0 if current_count > 0 else 0
            else:
                percentage = ((current_count - previous_count) / previous_count) * 100

            result[source] = {
                "current": current_count,
                "previous": previous_count,
                "percentage_change": round(percentage, 2)
            }

        return Response(result)


class SourceListAPIView(generics.CreateAPIView):
    queryset=Source.objects.all
    serializer_class=SourceModelSerializer