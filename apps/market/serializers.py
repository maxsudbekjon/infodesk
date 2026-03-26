from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.market.models import MarketOrder, Product
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
        fields = ("id", "image", "title", "price", "description")

    @extend_schema_field(OpenApiTypes.URI)
    def get_image(self, obj):
        request = self.context.get("request")
        return build_product_image_url(obj, request=request)


class MarketOrderSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True)
    product_id = serializers.IntegerField(source="product.id", read_only=True)
    product_title = serializers.CharField(source="product.title", read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = MarketOrder
        fields = (
            "id",
            "product",
            "product_id",
            "product_title",
            "product_image",
            "price",
            "secret_code",
            "created_at",
        )
        read_only_fields = ("product_id", "product_title", "product_image", "price", "secret_code", "created_at")

    @extend_schema_field(OpenApiTypes.URI)
    def get_product_image(self, obj):
        request = self.context.get("request")
        return build_product_image_url(obj.product, request=request)

    def create(self, validated_data):
        request = self.context.get("request")
        student = get_student_profile(getattr(request, "user", None))

        if not student:
            raise serializers.ValidationError({"detail": "Bu endpoint faqat student account uchun."})

        return MarketOrder.objects.create(student=student, **validated_data)
