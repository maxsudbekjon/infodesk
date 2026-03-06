from django.db import models

from apps.base_models import TimeStampedModel
from apps.pupil.choices import STUDENT_PAYMENT


class Student(TimeStampedModel):
    lead = models.ForeignKey("lead.Lead", on_delete=models.CASCADE)
    grade = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    next_payment_date = models.DateField(null=True, blank=True)
    # Lead da ham groups bor.
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=30,
        choices=STUDENT_PAYMENT.choices,
        default=STUDENT_PAYMENT.NO_DEBT,
    )
    comment = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["payment_status", "next_payment_date"], name="student_pay_date_idx"),
            models.Index(fields=["next_payment_date"], name="student_next_pay_idx"),
        ]

    def __str__(self) -> str:
        return self.lead.phone_number
