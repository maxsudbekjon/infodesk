from django.db import models
from django.utils import timezone


class StudentNote(models.Model):
    student = models.ForeignKey(
        "pupil.Student",
        on_delete=models.CASCADE,
        related_name="notes",
    )
    operator = models.ForeignKey(
        "user.Operator",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_notes",
    )
    text = models.TextField()
    date = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.text
