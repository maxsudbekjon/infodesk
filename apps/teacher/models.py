from django.db import models
from apps.base_models import TimeStampedModel
from config import settings




# class Teacher(TimeStampedModel):
#
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='teachers'
#     )
#     specialty = models.ManyToManyField(
#         Specialty,
#         related_name='teachers'
#     )
#     image = models.FileField(
#         upload_to='teacher-avatar',
#         null=True,
#         blank=True
#     )
#     monthly_salary = models.DecimalField(
#         max_digits=15,
#         decimal_places=2,
#         null=True,
#         blank=True
#     )
#     kpi = models.IntegerField(
#         null=True,
#         blank=True
#     )
#     monthly_per_lesson = models.DecimalField(
#         max_digits=15,
#         decimal_places=2,
#         null=True,
#         blank=True
#     )
#     monthly_per_student = models.DecimalField(
#         max_digits=15,
#         decimal_places=2,
#         null=True,
#         blank=True
#     )
#     is_archived  = models.BooleanField(
#         default=False
#     )
#
#     def __str__(self):
#         return self.user.phone_number



class Specialty(models.Model):

    title = models.CharField(
        max_length=255
    )

    def __str__(self):
        return self.title


from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

GENDER_CHOICES = (
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
)

class Teacher(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teachers'
    )
    specialty = models.ManyToManyField(
        Specialty,
        related_name='teachers',
        blank=True
    )
    image = models.FileField(
        upload_to='teacher-avatar',
        null=True,
        blank=True
    )

    # financial / contract fields
    monthly_salary = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    kpi = models.IntegerField(null=True, blank=True)
    monthly_per_lesson = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    monthly_per_student = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # suggested new fields
    contract_date = models.DateField(null=True, blank=True)
    percentage_share = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    lesson_fee = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    per_student_fee = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    branch = models.ForeignKey('settings.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='teachers')
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        # fall back if no user
        return getattr(self.user, 'phone_number', f'Teacher-{self.pk}')

