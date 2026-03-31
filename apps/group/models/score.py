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

    def save(self, *args, **kwargs):
        previous_student_id = None
        if self.pk:
            previous_student_id = (
                type(self).objects.filter(pk=self.pk).values_list("student_id", flat=True).first()
            )

        super().save(*args, **kwargs)

        from apps.pupil.coin import recalculate_student_total_coin

        for student_id in {previous_student_id, self.student_id}:
            if student_id:
                recalculate_student_total_coin(student_id)

    def delete(self, *args, **kwargs):
        student_id = self.student_id
        super().delete(*args, **kwargs)

        if student_id:
            from apps.pupil.coin import recalculate_student_total_coin

            recalculate_student_total_coin(student_id)

    def __str__(self) -> str:
        return f"{self.student} - {self.score}"
