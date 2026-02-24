from django.db import models
from apps.base_models import TimeStampedModel
from config import settings



class Specialty(models.Model):

    title = models.CharField(
        max_length=255
    )

    def __str__(self):
        return self.title


class Teacher(TimeStampedModel):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teachers'
    )
    specialty = models.ManyToManyField(
        Specialty,
        related_name='teachers'
    )
    image = models.FileField(
        upload_to='teacher-avatar',
        null=True,
        blank=True
    )
    monthly_salary = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    kpi = models.IntegerField(
        null=True,
        blank=True
    )
    monthly_per_lesson = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    monthly_per_student = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_archived  = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.user.phone_number
