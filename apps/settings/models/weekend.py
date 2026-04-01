from django.db import models
from django.contrib.auth import get_user_model

from apps.base_models import TimeStampedModel
from apps.settings.models.branch import Branch


User = get_user_model()


class Weekend(TimeStampedModel):
    branch = models.ForeignKey(Branch, related_name="weekends", on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    reason = models.TextField(blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ("branch", "date")

    def __str__(self) -> str:
        return f"{self.date} — {self.branch.name if self.branch else 'Global'}"
