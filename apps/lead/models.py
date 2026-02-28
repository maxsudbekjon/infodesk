from django.db import models
from apps.base_models import TimeStampedModel
from apps.group.choices import GROUP_DAYS_CHOICES
from apps.lead.choices import LEAD_SOURCE, LEAD_STATUS, LEAD_TEMPERATURE
from config import settings
from django.db.models import Q




class Situation(models.Model):

    organization = models.ForeignKey('settings.Organization',on_delete=models.CASCADE,null=True,blank=True)
    title = models.CharField(
        max_length=255
    )
    is_static  = models.BooleanField(default=False)


    def __str__(self):
        return self.title


class Lead(TimeStampedModel):
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=30)
    group = models.ForeignKey(
        'group.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    course = models.ForeignKey(
        'group.CourseTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )
    operator = models.ForeignKey(
        'user.Operator',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )
    center = models.ForeignKey(
        'settings.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lead'

    )
    days = models.ManyToManyField(
        'group.Day',
        related_name='leads',
        null=True,
        blank=True
    )
    days_choice = models.CharField(
        max_length=30,
        choices=GROUP_DAYS_CHOICES.choices,
        null=True,
        blank=True
    )
    prefer_time = models.TimeField(null=True,blank=True)
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
    comment = models.TextField(null=True,blank=True)
    is_active = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(is_active=True, is_archived=True),
                name="prevent_active_and_archived_true"
            )
        ]

        indexes = [
            models.Index(fields=['center', 'status'], name='lead_center_status_idx'),
            models.Index(fields=['center', '-created_at'], name='lead_center_created_idx'),
            models.Index(fields=['operator', 'status'], name='lead_operator_status_idx'),
            models.Index(fields=['course'], name='lead_course_idx'),
            models.Index(fields=['phone_number'], name='lead_phone_idx'),
        ]
        
    def save(self, *args, **kwargs):
        if self.course and not self.center:
            branch = self.course.branch
            if branch:
                self.center = branch.organization
        super().save(*args, **kwargs)
    def __str__(self):
        return self.phone_number


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
