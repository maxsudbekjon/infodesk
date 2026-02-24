from django.db import models
from apps.groups.choices import GROUP_DAYS_CHOICES, GROUP_STATUS




class Course(models.Model):

    title = models.CharField(
        max_length=255
    )
    price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,


        blank=True
    )

    def __str__(self):
        return self.title
    

class Day(models.Model):

    day = models.CharField(
        max_length=255
    )

    def __str__(self):
        return self.day


class Room(models.Model):

    title=models.CharField(
        max_length=255
    )
    
    def __str__(self):
        return self.title
    

class Group(models.Model):

    title = models.CharField(
        max_length=255
    )
    course = models.ForeignKey(
        Course,
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
    create_at=models.DateField(
        auto_now_add=True
    )
    closed_at=models.DateField(
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_lesson__lt=models.F('end_lesson')),
                name='group_start_before_end_lesson',
            ),
        ]
        indexes = [
            models.Index(fields=['status', 'create_at'], name='group_status_date_idx'),
            models.Index(fields=['teacher', 'status'], name='group_teacher_status_idx'),
        ]

    def __str__(self):
        return self.title
