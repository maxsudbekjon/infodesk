from django.core.cache import cache
from rest_framework import generics
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from apps.lead.models import Situation
from apps.lead.serializers import SituationModelSerializer

@extend_schema(tags=['Lead'])
class SituationCreateAPIView(generics.CreateAPIView):
    queryset = Situation.objects.all()
    serializer_class = SituationModelSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        organization = serializer.validated_data.get("organization")
        if not organization:
            raise ValidationError({"organization": "Organization majburiy."})

        if organization.owner_id != self.request.user.id:
            raise ValidationError({"organization": "Faqat o'zingizga tegishli organization uchun qo'sha olasiz."})

        serializer.save()

@extend_schema(tags=['Lead'])
class SituationListAPIView(generics.ListAPIView):
    serializer_class = SituationModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        organizations = user.organization.all()

        if not organizations.exists():
            return Situation.objects.filter(is_static=True)

        return Situation.objects.filter(
            Q(organization__in=organizations) | Q(is_static=True)
        ).select_related("organization").distinct()