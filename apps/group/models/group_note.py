from django.conf import settings

from apps.base_models import TimeStampedModel
from django.db import models


class GroupNote(TimeStampedModel):
    group = models.ForeignKey(
        'group.Group',
        on_delete=models.CASCADE,
        related_name='notes'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='group_notes'
    )
    text = models.TextField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note by {self.author} for {self.group.title}"