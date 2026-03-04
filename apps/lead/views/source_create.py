from rest_framework import generics
from drf_spectacular.utils import extend_schema
from apps.lead.models import Source
from apps.lead.serializers import SourceModelSerializer

@extend_schema(tags=['Lead'])
class SourceCreateAPIView(generics.CreateAPIView):
    queryset = Source.objects.all
    serializer_class = SourceModelSerializer
