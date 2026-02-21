from django.db import models

from apps.puplis.choices import STUDENT_PAYMENT




# Create your models here.
class Student(models.Model):
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.CASCADE
    )
    grade = models.DecimalField(max_digits=20,decimal_places=2)
    next_payment_date = models.DateField()
    groups = models.ManyToManyField(
        'groups.Group',
        related_name='students'
    )
    balanse = models.DecimalField(
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
    commit = models.TextField()


    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.username
    

class Parents(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )