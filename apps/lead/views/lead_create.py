from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.lead.models import Lead
from apps.lead.serializers import LeadModelSerializer

@extend_schema(tags=['Lead'])
class LeadCreateAPIView(generics.CreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadModelSerializer
    permission_classes = [IsAuthenticated]
