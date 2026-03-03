from django.db import models

from apps.base_models import TimeStampedModel
from apps.user.models.user import User


class Operator(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    center = models.ForeignKey("settings.Organization", on_delete=models.CASCADE)
    image = models.FileField(upload_to="teacher-avatar", null=True, blank=True)
    monthly_salary = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    kpi = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    is_archived = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.user.phone_number
