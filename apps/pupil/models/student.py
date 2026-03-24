from django.db import models
from django.conf import settings
import re
from django.core.exceptions import ValidationError
from apps.base_models import TimeStampedModel
from apps.pupil.choices import DISCOUNT_TYPE, STUDENT_PAYMENT, TRANSFER_REASON
from apps.pupil.choices import STUDENT_STATUS


def validate_phone_number(value):
    pattern = r'^\+\d{7,15}$'
    if not re.match(pattern, str(value)):
        raise ValidationError(
            f'"{value}" is not a valid phone number. '
            'Use international format, e.g. +12334556 or +998903314222'
        )

class Student(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
    )
    lead = models.ForeignKey("lead.Lead", on_delete=models.SET_NULL,null=True,blank=True)
    full_name = models.CharField(max_length=100,null=True,blank=True)
    next_payment_date = models.DateField(null=True, blank=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=30,
        choices=STUDENT_PAYMENT.choices,
        default=STUDENT_PAYMENT.NO_DEBT,
    )
    phone_number = models.CharField(max_length=30,validators=[validate_phone_number],null=True,blank=True)
    comment = models.TextField(null=True, blank=True)
    group = models.ForeignKey(
        "group.Group",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status=models.CharField(max_length=20,choices=STUDENT_STATUS.choices,default=STUDENT_STATUS.ACTIVE)
    center = models.ForeignKey(
        "settings.Organization",
        on_delete=models.CASCADE,
        related_name="students",
        null=True,
        blank=True
    )
    class Meta:
        indexes = [
            models.Index(fields=["payment_status", "next_payment_date"], name="student_pay_date_idx"),
            models.Index(fields=["next_payment_date"], name="student_next_pay_idx"),
        ]
    def save(self, *args, **kwargs):
        if self.lead:
            if not self.full_name:
                self.full_name = self.lead.full_name

            if not self.phone_number:
                self.phone_number = self.lead.phone_number

            if not self.group:
                self.group = self.lead.group

            if not self.center:
                self.center = self.lead.center

        super().save(*args, **kwargs)

    @property
    def latest_grade(self):
        latest = self.grades.order_by("-date").first()
        return latest.grade if latest else None

    @property
    def average_grade(self):
        grades = self.grades.values_list("grade", flat=True)
        if not grades:
            return None
        return sum(grades) / len(grades)

    def __str__(self) -> str:
        if self.full_name:
            return self.full_name
        if self.phone_number:
            return self.phone_number
        return f"Student {self.id}"


class StudnetTransfer(models.Model):
    student=models.ForeignKey(Student,on_delete=models.CASCADE)
    from_group=models.ForeignKey(
        'group.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_transfers_from',
    )
    to_group=models.ForeignKey(
        'group.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_transfers_to',
    )
    from_branch=models.ForeignKey(
        'settings.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_transfers_from',
    )
    to_branch=models.ForeignKey(
        'settings.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_transfers_to',
    )
    reason=models.TextField()
    reason_choice=models.CharField(max_length=30,choices=TRANSFER_REASON.choices,null=True,blank=True)
    is_apply_discount=models.BooleanField(default=False)
    is_debt=models.BooleanField(default=False)
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    discount_type=models.CharField(max_length=30,choices=DISCOUNT_TYPE.choices,null=True,blank=True)
    specific_month = models.IntegerField(
        null=True,
        blank=True
    )


    def __str__(self):
        return f"{self.from_group} -> {self.to_group}"
