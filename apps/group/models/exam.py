from django.db import models


class Exam(models.Model):
    group = models.ForeignKey(
        "group.Group",
        on_delete=models.CASCADE,
        related_name="exams",
    )
    title = models.CharField(max_length=255)
    date = models.DateField()
    pass_score = models.DecimalField(max_digits=6, decimal_places=2)
    max_score = models.DecimalField(max_digits=6, decimal_places=2)
    note = models.TextField(null=True, blank=True)
    extra_data = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["group", "date"], name="exam_group_date_idx"),
            models.Index(fields=["date"], name="exam_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.title} - {self.date}"
