from django.db import models

from apps.base_models import TimeStampedModel


class PaymentMethod(TimeStampedModel):
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=50, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name
