from django.db import models
from django.utils import timezone


class GroupScore(models.Model):
    group = models.ForeignKey(
        "group.Group",
        on_delete=models.CASCADE,
        related_name="scores",
    )
    student = models.ForeignKey(
        "pupil.Student",
        on_delete=models.CASCADE,
        related_name="scores",
    )
    score = models.IntegerField()
    reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["group", "student"], name="score_group_student_idx"),
            models.Index(fields=["created_at"], name="score_created_at_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.student} - {self.score}"
