from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from apps.dashboard.admin_utils import FriendlyAdminMixin
from .models import Branch, Organization, PaymentMethod, ReceiptSettings, Weekend


@admin.register(Organization)
class OrganizationAdmin(FriendlyAdminMixin):
    list_display = (
        "id",
        "name",
        "owner",
        "organization_phone",
        "lead_consolidation",
        "grading_system",
        "cash_balance",
        "terminal_balance",
        "created_at",
    )
    list_filter = ("lead_consolidation", "grading_system", "created_at")
    search_fields = ("name", "organization_phone", "owner__phone_number", "owner__full_name", "address")
    search_help_text = "Organization nomi, telefon yoki owner bo'yicha qidiring."
    autocomplete_fields = ("owner",)
    list_select_related = ("owner",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("name", "owner", "organization_phone", "description", "logo"),
        }),
        ("Manzil", {
            "fields": ("address", "latitude", "longitude"),
        }),
        ("Ishlash sozlamalari", {
            "fields": ("lead_consolidation", "grading_system", "sms_identifier"),
        }),
        ("Hisob-kitob", {
            "fields": ("cash_balance", "terminal_balance", "bank_accounts"),
        }),
        ("Texnik ma'lumotlar", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(Branch)
class BranchAdmin(FriendlyAdminMixin):
    list_display = (
        "id",
        "name",
        "organization",
        "phone",
        "manager",
        "is_active",
        "cash_balance",
        "terminal_balance",
        "created_at",
    )
    list_filter = ("is_active", "organization", "created_at")
    search_fields = ("name", "phone", "organization__name", "manager__phone_number", "address")
    search_help_text = "Filial nomi, telefon, organization yoki manager bo'yicha qidiring."
    autocomplete_fields = ("organization", "manager")
    filter_horizontal = ("courses",)
    list_select_related = ("organization", "manager")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("organization", "name", "phone", "manager", "is_active"),
        }),
        ("Kurslar va manzil", {
            "fields": ("courses", "address", "latitude", "longitude"),
        }),
        ("Hisob-kitob", {
            "fields": ("cash_balance", "terminal_balance", "bank_accounts", "sms_identifier"),
        }),
        ("Texnik ma'lumotlar", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(ReceiptSettings)
class ReceiptSettingsAdmin(FriendlyAdminMixin):
    list_display = (
        "id",
        "branch",
        "organization",
        "show_logo",
        "show_payment_id",
        "show_qr_code",
        "logo_position",
        "created_at",
    )
    list_filter = ("show_logo", "show_qr_code", "show_payment_id", "logo_position", "created_at")
    search_fields = ("branch__name", "organization__name", "top_text", "footer_text")
    search_help_text = "Receipt settings ni filial yoki organization bo'yicha qidiring."
    autocomplete_fields = ("branch", "organization")
    list_select_related = ("branch", "organization")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PaymentMethod)
class PaymentMethodAdmin(FriendlyAdminMixin):
    list_display = ("id", "name", "code", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "code")
    search_help_text = "To'lov usulini nomi yoki kodi bo'yicha qidiring."
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Weekend)
class WeekendAdmin(FriendlyAdminMixin):
    list_display = ("id", "branch", "date", "created_by", "reason")
    list_filter = ("branch", "date")
    search_fields = ("branch__name", "created_by__phone_number", "reason")
    search_help_text = "Dam olish kunini filial, yaratuvchi yoki sabab bo'yicha qidiring."
    autocomplete_fields = ("branch", "created_by")
    list_select_related = ("branch", "created_by")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")


def _register_all_models():
    app_config = django_apps.get_app_config("settings")
    for model in app_config.get_models():
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            pass


_register_all_models()
