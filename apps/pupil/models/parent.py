from django.db import models
import re
from django.core.exceptions import ValidationError


from apps.pupil.models.student import Student
def validate_phone_number(value):
    pattern = r'^\+\d{7,15}$'
    if not re.match(pattern, str(value)):
        raise ValidationError(
            f'"{value}" is not a valid phone number. '
            'Use international format, e.g. +12334556 or +998903314222'
        )

class Parent(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255,validators=[validate_phone_number])
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name
