from django.db import models
from django.db.models import CASCADE

from apps.base_models import TimeStampedModel
from apps.group.choices import GROUP_DAYS_CHOICES, GROUP_STATUS


class CourseTemplate(TimeStampedModel):
    

    name = models.CharField(max_length=255)
    note = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    duration_months = models.PositiveIntegerField(default=1)
    
    center = models.ForeignKey('settings.Organization',on_delete=models.CASCADE,
                               related_name="course_templates")


def __str__(self):
    return f"{self.name} — {self.branch.name if self.branch else 'Global'}"


class Day(models.Model):
    day = models.CharField(
        max_length=255
    )

    def __str__(self):
        return self.day


class Room(TimeStampedModel):
    branch = models.ForeignKey('settings.Branch', related_name="rooms", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class Group(TimeStampedModel):
    title = models.CharField(
        max_length=255
    )
    course = models.ForeignKey(
        CourseTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='groups'
    )
    branch = models.ForeignKey(
        'settings.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='group'
    )
    teacher = models.ForeignKey(
        'teacher.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='main_groups'
    )
    assistant_teacher = models.ForeignKey(
        'teacher.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assistant_group'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    lessons_days_choice = models.CharField(
        max_length=30,
        choices=GROUP_DAYS_CHOICES.choices,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=30,
        choices=GROUP_STATUS.choices,
        default=GROUP_STATUS.ACTIVE
    )
    lessons_days = models.ManyToManyField(
        Day,
        related_name='groups',
        blank=True
    )
    start_lesson = models.TimeField()
    end_lesson = models.TimeField()
    total_student = models.IntegerField(
        default=0
    )
    started_at = models.DateField(
        null=True,
        blank=True
    )
    closed_at = models.DateField(
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(start_lesson__lt=models.F('end_lesson')),
                name='group_start_before_end_lesson',
            ),
            models.CheckConstraint(
                condition=models.Q(started_at__lt=models.F('closed_at')),
                name='group_start_date_before_end_date',
            ),
        ]
        indexes = [
            models.Index(fields=['status', 'created_at'], name='group_status_date_idx'),
            models.Index(fields=['teacher', 'status'], name='group_teacher_status_idx'),
            models.Index(fields=['course', 'branch'], name='group_course_branch_idx'),
            models.Index(fields=['branch'], name='group_branch_idx'),
            models.Index(fields=['branch', 'status'], name='group_branch_status_idx'),
        ]

    def __str__(self):
        return self.title
