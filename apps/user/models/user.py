import re

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import identify_hasher, is_password_usable, make_password
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from apps.user.choices import GENDER, ROLE


def validate_phone_number(value):
    pattern = r'^\+\d{7,15}$'
    if not re.match(pattern, str(value)):
        raise ValidationError(
            f'"{value}" is not a valid phone number. '
            'Use international format, e.g. +12334556 or +998903314222'
        )


def split_full_name_parts(full_name: str | None) -> tuple[str, str]:
    cleaned_name = " ".join((full_name or "").split())
    if not cleaned_name:
        return "", ""

    parts = cleaned_name.split()
    if len(parts) == 1:
        return parts[0], ""

    suffix_tokens = {"o'g'li", "oʻgʻli", "ugli", "ogli", "qizi", "kyzy", "qyzy"}
    last_token = parts[-1].lower()
    if len(parts) >= 3 and last_token in suffix_tokens:
        first_name = " ".join(parts[-2:])
        last_name = " ".join(parts[:-2])
        return first_name, last_name

    first_name = parts[-1]
    last_name = " ".join(parts[:-1])
    return first_name, last_name


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

    def get_full_name(self):
        if self.full_name and self.full_name.strip():
            return self.full_name.strip()

        fallback_name = super().get_full_name().strip()
        if fallback_name:
            return fallback_name

        return self.phone_number or ""

    @property
    def display_name(self):
        return self.get_full_name()

    def save(self, *args, **kwargs):
        cleaned_full_name = " ".join((self.full_name or "").split())
        if cleaned_full_name:
            self.full_name = cleaned_full_name
            if not self.first_name and not self.last_name:
                self.first_name, self.last_name = split_full_name_parts(cleaned_full_name)
        else:
            fallback_name = super().get_full_name().strip()
            if fallback_name:
                self.full_name = fallback_name

        if self.password and is_password_usable(self.password):
            try:
                identify_hasher(self.password)
            except ValueError:
                self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.phone_number}"
