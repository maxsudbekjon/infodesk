from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.lead.models import Lead


class LeadDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Lead
    lookup_field = "id"
