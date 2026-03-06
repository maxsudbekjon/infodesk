import re

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import identify_hasher, is_password_usable, make_password
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from apps.user.choices import GENDER, ROLE
import re
from django.core.exceptions import ValidationError


def validate_phone_number(value):
    pattern = r'^\+\d{7,15}$'
    if not re.match(pattern, str(value)):
        raise ValidationError(
            f'"{value}" is not a valid phone number. '
            'Use international format, e.g. +12334556 or +998903314222'
        )

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValidationError("phone_number is required")


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
    full_name = models.CharField(max_length=255, null=True, blank=True)

    phone_number = models.CharField(max_length=20, unique=True,validators=[validate_phone_number])
    phone_number2 = models.CharField(max_length=20, unique=True, null=True, blank=True,validators=[validate_phone_number])

    gender = models.CharField(max_length=30, choices=GENDER.choices, null=True, blank=True)
    role = models.CharField(max_length=30, choices=ROLE.choices, default=ROLE.USER)
    birthday = models.DateField(blank=True, null=True)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.password and is_password_usable(self.password):
            try:
                identify_hasher(self.password)
            except ValueError:
                self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.phone_number}"
