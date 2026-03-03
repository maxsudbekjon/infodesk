from django.db import models

from apps.lead.models.lead import Lead


class Note(models.Model):
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    operator = models.ForeignKey("user.Operator", on_delete=models.CASCADE)
    text = models.TextField()
    date = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.text
