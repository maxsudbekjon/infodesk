from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.lead.models import Lead

@extend_schema(tags=['Lead'])
class LeadDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Lead.objects.all()
    lookup_field = "id"
