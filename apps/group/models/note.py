from django.db import models
from django.utils import timezone


class GroupNote(models.Model):
    group = models.ForeignKey(
        "group.Group",
        on_delete=models.CASCADE,
        related_name="notes",
    )
    author_name = models.CharField(max_length=150, null=True, blank=True)
    text = models.TextField()
    date = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.text
