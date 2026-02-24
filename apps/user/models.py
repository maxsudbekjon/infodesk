from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
import re
from apps.base_models import TimeStampedModel
from apps.user.choices import GENDER, ROLE




class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValidationError("phone_number is required")

        # Minimal phone format check (starts with + and digits only)
        if not re.match(r"^\+?\d{7,15}$", phone_number):
            raise ValidationError({"phone_number": "Telefon raqami noto‘g‘ri formatda!"})

        extra_fields["phone_number"] = phone_number
        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    username = None

    phone_number = models.CharField(max_length=20, unique=True)
    gender=models.CharField(
        max_length=30,
        choices=GENDER.choices,
        null=True,
        blank=True
    )
    role = models.CharField(max_length=30,choices=ROLE.choices,default=ROLE.USER)
    birthday = models.DateField(
        blank=True,
        null=True
    )

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.phone_number}"


class Operator(TimeStampedModel):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
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
    kpi = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    is_archived  = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.user.phone_number
