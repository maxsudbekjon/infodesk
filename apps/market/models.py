import secrets
import string

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db import models

from apps.base_models import TimeStampedModel
from apps.pupil.models import Student


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

    def _price_coin(self) -> int:
        return int(self.price or 0)

    def _refund_reserved_coin(self) -> None:
        locked_student = Student.objects.select_for_update().only(
            "id",
            "used_coin",
            "total_coin",
        ).get(pk=self.student_id)
        locked_product = Product.objects.select_for_update().only("id", "count").get(pk=self.product_id)
        price_coin = self._price_coin()

        locked_student.used_coin = max(int(locked_student.used_coin or 0) - price_coin, 0)
        locked_student.total_coin = int(locked_student.total_coin or 0) + price_coin
        locked_student.save(update_fields=["used_coin", "total_coin"])

        locked_product.count += 1
        locked_product.save(update_fields=["count"])

    def _reserve_coin_again(self) -> None:
        locked_student = Student.objects.select_for_update().only(
            "id",
            "used_coin",
            "total_coin",
        ).get(pk=self.student_id)
        locked_product = Product.objects.select_for_update().only("id", "count").get(pk=self.product_id)
        price_coin = self._price_coin()

        if locked_product.count < 1:
            raise ValidationError("Bu mahsulot tugagan.")
        if int(locked_student.total_coin or 0) < price_coin:
            raise ValidationError("Studentda coin yetarli emas.")

        locked_student.used_coin = int(locked_student.used_coin or 0) + price_coin
        locked_student.total_coin = int(locked_student.total_coin or 0) - price_coin
        locked_student.save(update_fields=["used_coin", "total_coin"])

        locked_product.count -= 1
        locked_product.save(update_fields=["count"])

    def save(self, *args, **kwargs):
        previous_status = None
        if self.pk:
            previous_status = (
                type(self).objects.filter(pk=self.pk).values_list("status", flat=True).first()
            )

        if self.product_id and not self.price:
            self.price = self.product.price

        if not self.secret_code:
            self.secret_code = generate_secret_code()

        with transaction.atomic():
            super().save(*args, **kwargs)

            if previous_status == MARKET_ORDER_STATUS.CREATED and self.status == MARKET_ORDER_STATUS.CANCELLED:
                self._refund_reserved_coin()
            elif previous_status == MARKET_ORDER_STATUS.CANCELLED and self.status in {
                MARKET_ORDER_STATUS.CREATED,
                MARKET_ORDER_STATUS.DELIVERED,
            }:
                self._reserve_coin_again()

    def __str__(self) -> str:
        return f"{self.student} - {self.product} - {self.secret_code}"
