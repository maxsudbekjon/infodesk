from rest_framework import generics

from apps.lead.models import Lead
from apps.lead.serializers import LeadAddGroupSerializer


class LeadAddGroupAPIView(generics.UpdateAPIView):
    queryset = Lead
    serializer_class = LeadAddGroupSerializer
    lookup_field = "id"
