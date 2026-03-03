from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.lead.models import Situation
from apps.lead.serializers import SituationModelSerializer


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
