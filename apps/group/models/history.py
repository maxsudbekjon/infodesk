from django.db import models
from django.utils import timezone


class GroupHistory(models.Model):
    group = models.ForeignKey(
        "group.Group",
        on_delete=models.CASCADE,
        related_name="history",
    )
    title = models.CharField(max_length=255)
    old_value = models.CharField(max_length=255, null=True, blank=True)
    new_value = models.CharField(max_length=255, null=True, blank=True)
    author_name = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    extra_data = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["group", "created_at"], name="history_group_date_idx"),
        ]

    def __str__(self) -> str:
        return self.title
