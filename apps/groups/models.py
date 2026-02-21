from django.db import models

from apps.groups.choices import GROUP_DAYS_CHOICES, GROUP_STATUS

# Create your models here.
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
    
class Days(models.Model):

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
    

class Groups(models.Model):

    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    teacher = models.ForeignKey(
        'teacher.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    assistant_teacher=models.ForeignKey(
        'teacher.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True 
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
    lessons_days=models.ManyToManyField(
        Days,
        related_name='groups',
        null=True,
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
        auto_now_add=True
    )
    status=models.CharField(max_length=30,choices=GROUP_STATUS.choices,default=GROUP_STATUS.ACTIVE)




