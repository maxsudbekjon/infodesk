from django.db import models
from apps.base_models import TimeStampedModel
from apps.puplis.choices import STUDENT_PAYMENT




class Student(TimeStampedModel):
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.CASCADE
    )
    grade = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )
    next_payment_date = models.DateField()
    groups = models.ManyToManyField(
        'groups.Group',
        related_name='students'
    )
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2
    )
    payment_status=models.CharField(
        max_length=30,
        choices=STUDENT_PAYMENT.choices,
        default=STUDENT_PAYMENT.NO_DEBT  
    )
    attendance = models.DecimalField(
        max_digits=3,
        decimal_places=2
    )
    comment = models.TextField()


    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(attendance__gte=0) & models.Q(attendance__lte=100),
                name='student_attendance_between_0_and_100',
            ),
        ]

    def __str__(self):
        return self.lead.user.phone_number
    

class Parents(models.Model):
    name = models.CharField(
        max_length=255
    )
    phone_number = models.CharField(
        max_length=255
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )
    def __str__(self):
        return self.name
