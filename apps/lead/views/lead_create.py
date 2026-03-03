from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.lead.models import Lead
from apps.lead.serializers import LeadModelSerializer


class LeadCreateAPIView(generics.CreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadModelSerializer
    permission_classes = [IsAuthenticated]
