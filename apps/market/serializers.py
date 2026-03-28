from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.group.models.score import GroupScore
from apps.market.models import MarketOrder, Product
from apps.pupil.models import Student
from apps.user.profile_resolver import get_student_profile


def build_product_image_url(product, request=None):
    image = getattr(product, "image", None)
    if not image:
        return None

    if request:
        return request.build_absolute_uri(image.url)

    return image.url


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id", "image", "title", "price", "description", "count")

    @extend_schema_field(OpenApiTypes.URI)
    def get_image(self, obj):
        request = self.context.get("request")
        return build_product_image_url(obj, request=request)


class MarketOrderSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True)
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    product_title = serializers.CharField(source="product.title", read_only=True)
    product_count = serializers.IntegerField(source="product.count", read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = MarketOrder
        fields = (
            "id",
            "product",
            "product_id",
            "product_title",
            "product_count",
            "product_image",
            "price",
            "status",
            "secret_code",
            "created_at",
        )
        read_only_fields = (
            "product_id",
            "product_title",
            "product_count",
            "product_image",
            "price",
            "status",
            "secret_code",
            "created_at",
        )

    @extend_schema_field(OpenApiTypes.URI)
    def get_product_image(self, obj):
        request = self.context.get("request")
        return build_product_image_url(obj.product, request=request)

    def create(self, validated_data):
        request = self.context.get("request")
        student = get_student_profile(getattr(request, "user", None))

        if not student:
            raise serializers.ValidationError({"detail": "Bu endpoint faqat student account uchun."})

        with transaction.atomic():
            locked_student = Student.objects.select_for_update().only("id", "used_coin").get(pk=student.pk)
            product = (
                Product.objects.select_for_update()
                .only("id", "title", "price", "count", "image")
                .get(pk=validated_data["product"].pk)
            )

            if product.count < 1:
                raise serializers.ValidationError({"product": "Bu mahsulot tugagan."})

            if product.price != product.price.to_integral_value():
                raise serializers.ValidationError(
                    {"product": "Mahsulot narxi coin uchun butun son bo'lishi kerak."}
                )

            earned_coin = (
                GroupScore.objects.filter(student_id=locked_student.id)
                .aggregate(total_coin=Coalesce(Sum("score"), 0))
                .get("total_coin", 0)
            )
            available_coin = max(earned_coin - locked_student.used_coin, 0)
            price_coin = int(product.price)

            if available_coin < price_coin:
                raise serializers.ValidationError({"product": "Studentda coin yetarli emas."})

            product.count -= 1
            product.save(update_fields=["count"])
            locked_student.used_coin += price_coin
            locked_student.save(update_fields=["used_coin"])

            return MarketOrder.objects.create(
                student=locked_student,
                product=product,
                price=product.price,
            )
