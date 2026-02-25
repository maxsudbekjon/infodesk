from django.db import models
from apps.base_models import TimeStampedModel
from apps.group.choices import GROUP_DAYS_CHOICES, GROUP_STATUS




class CourseTemplate(TimeStampedModel):
	GRADING_CHOICES = [
		("point", "Point"),
		("percent", "Percent"),
		("ielts", "IELTS"),
	]

	name = models.CharField(max_length=255)
	note = models.TextField(blank=True)
	price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	duration_months = models.PositiveIntegerField(default=1)
	grading_system = models.CharField(max_length=50, choices=GRADING_CHOICES, default="point")
	branch = models.ForeignKey('settings.Branch', null=True, blank=True, on_delete=models.CASCADE, related_name="course_templates")
	color_bg = models.CharField(max_length=7, default="#FFFFFF", help_text="Hex color for course background")
	color_text = models.CharField(max_length=7, default="#000000", help_text="Hex color for course text")
	price_effective_from = models.DateField(null=True, blank=True)
	apply_price_from_month = models.BooleanField(default=False, help_text="If true, apply price change from start of month for related groups")
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
    teacher = models.ForeignKey(
        'teacher.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='main_groups'
    )
    assistant_teacher=models.ForeignKey(
        'teacher.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assistant_group'
    )
    room=models.ForeignKey(
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
    status=models.CharField(
        max_length=30,
        choices=GROUP_STATUS.choices,
        default=GROUP_STATUS.ACTIVE
    )
    lessons_days=models.ManyToManyField(
        Day,
        related_name='groups',
        blank=True
    )
    start_lesson=models.TimeField()
    end_lesson=models.TimeField()
    students_count=models.IntegerField(
        default=0
    )

    closed_at=models.DateField(
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(start_lesson__lt=models.F('end_lesson')),
                name='group_start_before_end_lesson',
            ),
        ]
        indexes = [
            models.Index(fields=['status', 'created_at'], name='group_status_date_idx'),
            models.Index(fields=['teacher', 'status'], name='group_teacher_status_idx'),
        ]

    def __str__(self):
        return self.title
