from django.db import models


class Day(models.Model):
    day = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.day
