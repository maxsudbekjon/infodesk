from django.contrib import admin, messages
from django.utils.html import format_html

from apps.dashboard.admin_utils import FriendlyAdminMixin
from apps.market.models import MARKET_ORDER_STATUS, MarketOrder, Product


@admin.register(Product)
class ProductAdmin(FriendlyAdminMixin):
    admin_page_title = "Market mahsulotlari"
    admin_page_subtitle = "Sotuvdagi mahsulotlar, narx va qoldiqni boshqaring."
    list_display = ("id", "title", "price", "count", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "description")
    search_help_text = "Mahsulot nomi yoki tavsifi bo'yicha qidiring."
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("title", "image", "description"),
        }),
        ("Sotuv ma'lumotlari", {
            "fields": ("price", "count"),
        }),
        ("Texnik ma'lumotlar", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(MarketOrder)
class MarketOrderAdmin(FriendlyAdminMixin):
    admin_page_title = "Market buyurtmalari"
    admin_page_subtitle = "Mahsulot buyurtmalarini status bo'yicha boshqaring."
    list_display = (
        "id",
        "student",
        "student_phone",
        "product",
        "price",
        "status_badge",
        "secret_code",
        "created_at",
    )
    list_filter = ("status", "product", "created_at")
    search_fields = ("secret_code", "student__full_name", "student__phone_number", "product__title")
    search_help_text = "Buyurtmani kod, student yoki mahsulot bo'yicha qidiring."
    list_select_related = ("student", "product")
    autocomplete_fields = ("student", "product")
    actions = ("mark_as_delivered", "cancel_selected_orders")
    readonly_fields = ("secret_code", "price", "created_at", "updated_at")
    date_hierarchy = "created_at"

    @admin.display(description="Telefon")
    def student_phone(self, obj):
        return obj.student.phone_number

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        palette = {
            MARKET_ORDER_STATUS.CREATED: ("Yangi", "primary"),
            MARKET_ORDER_STATUS.DELIVERED: ("Qabul qilindi", "success"),
            MARKET_ORDER_STATUS.CANCELLED: ("Rad etildi", "danger"),
        }
        label, tone = palette.get(obj.status, (obj.get_status_display(), "info"))
        return format_html('<span class="status-badge status-badge--{}">{}</span>', tone, label)

    @admin.action(description="Tanlangan buyurtmalarni qabul qilish")
    def mark_as_delivered(self, request, queryset):
        updated = 0
        for order in queryset.exclude(status=MARKET_ORDER_STATUS.DELIVERED):
            order.status = MARKET_ORDER_STATUS.DELIVERED
            order.save(update_fields=["status"])
            updated += 1
        self.message_user(request, f"{updated} ta buyurtma qabul qilindi.", level=messages.SUCCESS)

    @admin.action(description="Tanlangan buyurtmalarni rad etish")
    def cancel_selected_orders(self, request, queryset):
        updated = 0
        for order in queryset.exclude(status=MARKET_ORDER_STATUS.CANCELLED):
            order.status = MARKET_ORDER_STATUS.CANCELLED
            order.save(update_fields=["status"])
            updated += 1
        self.message_user(request, f"{updated} ta buyurtma rad etildi.", level=messages.SUCCESS)
