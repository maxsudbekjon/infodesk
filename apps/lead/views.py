from django.shortcuts import render
from rest_framework import generics

from apps.lead.models import Lead
from apps.lead.serializers import LeadModelSerializer
# Create your views here.

class LeadCreateAPIView(generics.CreateAPIView):
    queryset=Lead.objects.all()
    serializer_class=LeadModelSerializer