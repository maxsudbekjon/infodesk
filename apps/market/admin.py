from django.contrib import admin

from apps.market.models import MarketOrder, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "price", "created_at")
    search_fields = ("title",)


@admin.register(MarketOrder)
class MarketOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "product", "price", "secret_code", "created_at")
    search_fields = ("secret_code", "student__full_name", "student__phone_number", "product__title")
    list_select_related = ("student", "product")
