import secrets
import string

from django.db import models

from apps.base_models import TimeStampedModel


def generate_secret_code():
    alphabet = string.ascii_uppercase + string.digits

    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        if not any(char.isalpha() for char in code):
            continue
        if not any(char.isdigit() for char in code):
            continue
        if not MarketOrder.objects.filter(secret_code=code).exists():
            return code


class Product(TimeStampedModel):
    image = models.ImageField(upload_to="market-product")
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title


class MARKET_ORDER_STATUS(models.TextChoices):
    CREATED = "created", "Created"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


class MarketOrder(TimeStampedModel):
    student = models.ForeignKey(
        "pupil.Student",
        on_delete=models.CASCADE,
        related_name="market_orders",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=MARKET_ORDER_STATUS.choices,
        default=MARKET_ORDER_STATUS.CREATED,
    )
    secret_code = models.CharField(max_length=6, unique=True, editable=False)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["student", "created_at"], name="market_order_student_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.product_id and not self.price:
            self.price = self.product.price

        if not self.secret_code:
            self.secret_code = generate_secret_code()

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.student} - {self.product} - {self.secret_code}"
