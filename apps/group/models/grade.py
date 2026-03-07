from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Grade(models.Model):
    group = models.ForeignKey(
        "group.Group",
        on_delete=models.CASCADE,
        related_name="grades",
    )
    student = models.ForeignKey(
        "pupil.Student",
        on_delete=models.CASCADE,
        related_name="grades",
    )
    date = models.DateField()
    grade = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    note = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "group", "date")
        indexes = [
            models.Index(fields=["group", "student"], name="grade_group_student_idx"),
            models.Index(fields=["date"], name="grade_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.student} - {self.group} - {self.date}: {self.grade}"
