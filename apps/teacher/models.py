from django.db import models




class Specialty(models.Model):

    title = models.CharField(
        max_length=255
    )

    def __str__(self):
        return self.title


# Create your models here.
class Teacher(models.Model):

    user = models.ForeignKey(
        'user.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
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
    birthday = models.DateField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    is_archived  = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.user.usename