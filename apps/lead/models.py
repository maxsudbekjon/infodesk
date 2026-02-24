from django.db import models
from apps.base_models import TimeStampedModel
from apps.group.choices import GROUP_DAYS_CHOICES
from apps.lead.choices import LEAD_SOURCE, LEAD_STATUS, LEAD_TEMPERATURE
from config import settings



class Situation(models.Model):
    # o'quv markaz yoki ceo acounti bog'lanadi. user/center (men yaratgan lead uchun bo'lim boshqalarda ko'rinmasligi uchun.)
    title = models.CharField(
        max_length=255
    )
    is_static  = models.BooleanField(default=False)
    def __str__(self):
        return self.title


class Lead(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    group = models.ForeignKey(
        'group.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    course = models.ForeignKey(
        'group.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )
    operator = models.ForeignKey(
        'user.Operator',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    center = models.ForeignKey(
        'dashboard.Center',
        on_delete=models.CASCADE,
        related_name='leads',
        null=True,
        blank=True,
    )
    days = models.ManyToManyField(
        'group.Day',
        related_name='leads'
    )
    days_choice = models.CharField(
        max_length=30,
        choices=GROUP_DAYS_CHOICES.choices,
        null=True,
        blank=True
    )
    situation = models.ForeignKey(
        Situation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=25,
        choices=LEAD_STATUS.choices,
        default=LEAD_STATUS.NEW
    )
    source = models.CharField(
        max_length=30,
        choices=LEAD_SOURCE.choices
    )
    temperature = models.CharField(max_length=20, choices=LEAD_TEMPERATURE.choices, default=LEAD_TEMPERATURE.HOT)
    comment = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at'], name='lead_user_created_idx'),
            models.Index(fields=['user', 'status'], name='lead_user_status_idx'),
            models.Index(fields=['center', '-created_at'], name='lead_center_created_idx'),
            models.index(fields=['center', 'status'], name='lead_center_status_idx'),
        ]

    def __str__(self):
        return self.user.phone_number


class Note(models.Model):
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    operator = models.ForeignKey(
        'user.Operator',
        on_delete=models.CASCADE
    )
    text = models.TextField()
    date = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.text
