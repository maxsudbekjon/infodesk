from django.db import models

from apps.base_models import TimeStampedModel


class CourseTemplate(TimeStampedModel):
    name = models.CharField(max_length=255)
    note = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    duration_months = models.PositiveIntegerField(default=1)

    center = models.ForeignKey(
        "settings.Organization",
        on_delete=models.CASCADE,
        related_name="course_templates",
    )

    def __str__(self) -> str:
        return self.name
