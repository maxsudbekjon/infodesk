from rest_framework import generics
from drf_spectacular.utils import extend_schema
from apps.lead.models import Lead
from apps.lead.serializers import LeadAddGroupSerializer



@extend_schema(tags=['Lead'])
class LeadAddGroupAPIView(generics.UpdateAPIView):
    queryset = Lead
    serializer_class = LeadAddGroupSerializer
    lookup_field = "id"
