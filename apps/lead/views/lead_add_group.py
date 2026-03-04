from rest_framework import generics
from drf_spectacular.utils import extend_schema
from apps.lead.models import Lead
from apps.lead.serializers import LeadAddGroupSerializer
from rest_framework.permissions import IsAuthenticated


@extend_schema(tags=['Lead'])
class LeadAddGroupAPIView(generics.UpdateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadAddGroupSerializer
    permission_classes=[IsAuthenticated]
    lookup_field = "id"
