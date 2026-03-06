from django.conf import settings
from django.db import models

from apps.base_models import TimeStampedModel
from apps.settings.choices import LEAD_CONSOLIDATION


class Organization(TimeStampedModel):
    GRADING_CHOICES = [
        ("point", "Point"),
        ("percent", "Percent"),
        ("ielts", "IELTS"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organization")
    # lead_consolidation - leadga operatorni qaysi usulda biriktirishni bildiradi.
    lead_consolidation = models.CharField(
        max_length=20,
        choices=LEAD_CONSOLIDATION.choices,
        default=LEAD_CONSOLIDATION.MANUAL,
    )
    organization_phone = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="organization/logos/", null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longtitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=1024, blank=True)
    sms_identifier = models.CharField(
        max_length=128,
        blank=True,
        help_text="Short name used when sending SMS from this branch",
    )
    bank_accounts = models.JSONField(
        blank=True, null=True, help_text="Optional bank account details JSON"
    )
    cash_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    terminal_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grading_system = models.CharField(
        max_length=50, choices=GRADING_CHOICES, default="point"
    )

    def __str__(self) -> str:
        return self.name
