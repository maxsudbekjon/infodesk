from django.db import models

from apps.base_models import TimeStampedModel
from apps.settings.models.branch import Branch
from apps.settings.models.organization import Organization


class ReceiptSettings(TimeStampedModel):
    LOGO_POSITION_TOP = "top"
    LOGO_POSITION_BOTTOM = "bottom"
    LOGO_POSITION_CHOICES = [
        (LOGO_POSITION_TOP, "Top"),
        (LOGO_POSITION_BOTTOM, "Bottom"),
    ]

    branch = models.OneToOneField(
        Branch, related_name="receipt_settings", on_delete=models.CASCADE, null=True, blank=True
    )
    organization = models.ForeignKey(
        Organization, related_name="receipt_settings", on_delete=models.CASCADE, null=True, blank=True
    )

    # Content
    top_text = models.TextField(blank=True, help_text="Text shown in the top part of receipt (address/phone)")
    footer_text = models.TextField(blank=True, help_text="Footer / thank you / social links")
    logo = models.ImageField(upload_to="receipts/logos/", null=True, blank=True)

    # Visual toggles
    show_logo = models.BooleanField(default=True)
    show_top_section = models.BooleanField(default=True)
    show_address = models.BooleanField(default=True)
    show_phone = models.BooleanField(default=True)
    show_print_time = models.BooleanField(default=True)
    show_payment_id = models.BooleanField(default=True)
    show_student_info = models.BooleanField(default=True)
    show_group_info = models.BooleanField(default=True)
    show_payment_form = models.BooleanField(default=True)
    show_payment_date = models.BooleanField(default=True)
    show_cashier = models.BooleanField(default=True)
    show_amount = models.BooleanField(default=True)
    show_footer = models.BooleanField(default=True)
    show_qr_code = models.BooleanField(default=True)
    show_teacher_name = models.BooleanField(default=False)
    show_course_price = models.BooleanField(default=False)

    logo_position = models.CharField(max_length=10, choices=LOGO_POSITION_CHOICES, default=LOGO_POSITION_TOP)

    class Meta:
        verbose_name = "Receipt Settings"
        verbose_name_plural = "Receipt Settings"

    def __str__(self) -> str:
        target = self.branch.name if self.branch else (self.organization.name if self.organization else "Global")
        return f"Receipt settings — {target}"
