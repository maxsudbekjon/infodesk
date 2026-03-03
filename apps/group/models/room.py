from django.db import models

from apps.base_models import TimeStampedModel


class Room(TimeStampedModel):
    branch = models.ForeignKey("settings.Branch", related_name="rooms", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.name} ({self.branch.name})"
