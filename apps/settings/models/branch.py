from django.db import models
from django.contrib.auth import get_user_model

from apps.base_models import TimeStampedModel
from apps.settings.models.organization import Organization


User = get_user_model()


class Branch(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, related_name="branches", on_delete=models.CASCADE
    )
    courses = models.ManyToManyField("group.CourseTemplate", related_name="branchs")
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=1024, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    sms_identifier = models.CharField(
        max_length=128,
        blank=True,
        help_text="Short name used when sending SMS from this branch",
    )
    is_active = models.BooleanField(default=True)
    manager = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="managed_branches",
    )
    bank_accounts = models.JSONField(
        blank=True, null=True, help_text="Optional bank account details JSON"
    )
    cash_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    terminal_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self) -> str:
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
