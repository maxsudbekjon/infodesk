from django.db import models


class GroupRankingComment(models.Model):
    group = models.ForeignKey(
        "group.Group",
        on_delete=models.CASCADE,
        related_name="ranking_comments",
    )
    student = models.ForeignKey(
        "pupil.Student",
        on_delete=models.CASCADE,
        related_name="ranking_comments",
    )
    comment = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("group", "student")
        indexes = [
            models.Index(fields=["group", "student"], name="ranking_group_student_idx"),
        ]

    def __str__(self) -> str:
        return self.comment
