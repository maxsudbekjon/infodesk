from django.db import models


class Source(models.Model):
    center = models.ForeignKey(
        "settings.Organization", on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=100)
    icon = models.ImageField(upload_to="sourse-icon")
    is_static = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(is_static=True, center__isnull=False),
                name="source_static_requires_no_org",
            )
        ]
    def __str__(self) -> str:
        return self.name
