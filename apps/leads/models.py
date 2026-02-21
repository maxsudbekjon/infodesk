from django.db import models
from apps.groups.choices import GROUP_DAYS_CHOICES
from apps.groups.models import Days
from apps.leads.choices import LEAD_SOURCE, LEAD_STATUS, LEAD_TEMPERATURE

# Create your models here.

class Situation(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Lead(models.Model):
    user = models.ForeignKey(
        'user.User',
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
        'groups.Days',
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
    commit = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.user.username


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
        return self.date
