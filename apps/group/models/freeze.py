from django.db import models
from django.utils import timezone


class GroupFreeze(models.Model):
    group = models.ForeignKey(
        "group.Group",
        on_delete=models.CASCADE,
        related_name="freezes",
    )
    reason = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["group", "start_date"], name="freeze_group_start_idx"),
            models.Index(fields=["group", "end_date"], name="freeze_group_end_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.group} frozen {self.start_date} - {self.end_date}"
