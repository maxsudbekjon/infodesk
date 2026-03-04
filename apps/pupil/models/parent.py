from django.db import models

from apps.pupil.models.student import Student


class Parent(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name
