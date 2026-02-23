from django.db import models
from apps.base_models import TimeStampedModel
from apps.groups.choices import GROUP_DAYS_CHOICES
from apps.leads.choices import LEAD_SOURCE, LEAD_STATUS, LEAD_TEMPERATURE
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
        'groups.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    operator = models.ForeignKey(
        'user.Operator',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    days = models.ManyToManyField(
        'groups.Day',
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
    source=models.CharField(
        max_length=30,
        choices=LEAD_SOURCE.choices
    )
    temperature=models.CharField(max_length=20,choices=LEAD_TEMPERATURE.choices,default=LEAD_TEMPERATURE.HOT)
    comment = models.TextField()

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
