from django.db import models
from django.utils import timezone


class GroupDiscount(models.Model):
    group = models.ForeignKey(
        "group.Group",
        on_delete=models.CASCADE,
        related_name="discounts",
    )
    student = models.ForeignKey(
        "pupil.Student",
        on_delete=models.CASCADE,
        related_name="discounts",
    )
    remaining_months = models.PositiveSmallIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    author_name = models.CharField(max_length=150, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    extra_data = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["group", "created_at"], name="discount_group_date_idx"),
            models.Index(fields=["student"], name="discount_student_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.student} - {self.price}"
