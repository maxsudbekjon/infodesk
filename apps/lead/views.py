from rest_framework import generics
from apps.lead.models import Lead
from apps.lead.serializers import LeadListModelSerializer, LeadModelSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError





# LeadListAPIView uchun
def parse_bool(value):
    value = value.lower()
    if value in ['true', '1', 'yes']:
        return True
    if value in ['false', '0', 'no']:
        return False
    raise ValidationError("Boolean qiymat noto‘g‘ri.")



class LeadPagination(PageNumberPagination):
    page_size = 2


class LeadCreateAPIView(generics.CreateAPIView):
    queryset=Lead.objects.all()
    serializer_class=LeadModelSerializer
    permission_classes=[IsAuthenticated]


class LeadListAPIView(generics.ListAPIView):
    serializer_class=LeadListModelSerializer
    pagination_class = LeadPagination
    def get_queryset(self):
        is_active = self.request.query_params.get('is_active')
        is_archived = self.request.query_params.get('is_archived')

        queryset = (
            Lead.objects
            .select_related(
                'user',
                'operator__user',
                'situation',
            )
            .only(
                'created_at',
                'situation',
                'user__first_name',
                'user__last_name',
                'user__phone_number',
                'operator__user__first_name',
                'operator__user__last_name',

            )
            .order_by('-created_at')
        )

        if is_active is not None:
            queryset = queryset.filter(
                is_active=parse_bool(is_active)
            )

        if is_archived is not None:
            queryset = queryset.filter(
                is_archived=parse_bool(is_archived)
            )

        return queryset