from django.db import models
from django.db.models import Q


class Situation(models.Model):
    organization = models.ForeignKey(
        "settings.Organization", on_delete=models.CASCADE, null=True, blank=True
    )
    title = models.CharField(max_length=255)
    is_static = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(is_static=True, organization__isnull=False),
                name="situation_static_requires_no_org",
            )
        ]

    def __str__(self) -> str:
        return self.title
