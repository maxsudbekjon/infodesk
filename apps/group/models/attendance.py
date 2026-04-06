from django.db import models
from apps.pupil.models.student import Student
from apps.group.models.group import Group


class Attendance(models.Model):
    group=models.ForeignKey(
        'group.Group',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    student = models.ForeignKey(
        'pupil.Student',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date = models.DateField()
    is_rise = models.BooleanField(default=False)
    is_present = models.BooleanField(null=True, blank=True, default=None)

    # Optional: Add a note for reasons behind absence
    note = models.TextField(null=True,blank=True)

    class Meta:
        unique_together = ('student', 'group', 'date')
        verbose_name_plural = "Attendance"
        indexes = [
            models.Index(fields=['group', 'student'], name='attendance_group_status_idx'),
            models.Index(fields=['is_present', 'date'], name='attendance_ispresent_date_idx'),
        ]

    def __str__(self):
        if self.is_present is True:
            status = 'Present'
        elif self.is_present is False:
            status = 'Absent'
        else:
            status = 'Unmarked'
        return f"{self.student} - {self.group.title} - {self.date}: {status}"
