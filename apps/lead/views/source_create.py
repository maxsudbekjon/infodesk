from rest_framework import generics

from apps.lead.models import Source
from apps.lead.serializers import SourceModelSerializer


class SourceCreateAPIView(generics.CreateAPIView):
    queryset = Source.objects.all
    serializer_class = SourceModelSerializer
