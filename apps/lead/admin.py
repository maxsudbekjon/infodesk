from django.contrib import admin, messages

from apps.dashboard.admin_utils import FriendlyAdminMixin
from apps.lead.models import Lead, Note, Situation, Source
from apps.lead.services import assign_for_new_lead


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0
    fields = ("text", "operator", "date")
    autocomplete_fields = ("operator",)


@admin.register(Lead)
class LeadAdmin(FriendlyAdminMixin):
    list_display = (
        "id",
        "full_name",
        "phone_number",
        "center",
        "status",
        "temperature",
        "operator",
        "course",
        "group",
        "is_active",
        "is_archived",
        "created_at",
    )
    list_filter = ("status", "temperature", "is_active", "is_archived", "center", "course", "source", "created_at")
    search_fields = (
        "full_name",
        "phone_number",
        "operator__user__full_name",
        "course__name",
        "group__title",
        "source__name",
    )
    search_help_text = "Lidni ism, telefon, kurs, guruh yoki manba bo'yicha qidiring."
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("center", "course", "operator__user", "group", "source", "situation")
    autocomplete_fields = ("course", "operator", "group", "center", "source", "situation")
    filter_horizontal = ("days",)
    inlines = (NoteInline,)
    actions = ("archive_selected", "unarchive_selected", "activate_selected", "deactivate_selected")
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("full_name", "phone_number", "center", "course", "group"),
        }),
        ("Aloqa va sotuv", {
            "fields": ("operator", "source", "situation", "status", "temperature", "comment"),
        }),
        ("Darsga moslash", {
            "fields": ("days_choice", "days", "prefer_time"),
        }),
        ("Holat", {
            "fields": ("is_active", "is_archived"),
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            assign_for_new_lead(obj)

    @admin.action(description="Tanlangan lidlarni arxivga o'tkazish")
    def archive_selected(self, request, queryset):
        updated = queryset.update(is_archived=True, is_active=False)
        self.message_user(request, f"{updated} ta lid arxivga o'tkazildi.", level=messages.SUCCESS)

    @admin.action(description="Tanlangan lidlarni arxivdan chiqarish")
    def unarchive_selected(self, request, queryset):
        updated = queryset.update(is_archived=False)
        self.message_user(request, f"{updated} ta lid arxivdan chiqarildi.", level=messages.SUCCESS)

    @admin.action(description="Tanlangan lidlarni active qilish")
    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True, is_archived=False)
        self.message_user(request, f"{updated} ta lid active qilindi.", level=messages.SUCCESS)

    @admin.action(description="Tanlangan lidlarni inactive qilish")
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} ta lid inactive qilindi.", level=messages.SUCCESS)


@admin.register(Situation)
class SituationAdmin(FriendlyAdminMixin):
    list_display = ("id", "title", "organization", "is_static")
    list_filter = ("is_static", "organization")
    search_fields = ("title", "organization__name")
    search_help_text = "Holatni nomi yoki organization bo'yicha qidiring."
    autocomplete_fields = ("organization",)


@admin.register(Source)
class SourceAdmin(FriendlyAdminMixin):
    list_display = ("id", "name", "center", "is_static")
    list_filter = ("is_static", "center")
    search_fields = ("name", "center__name")
    search_help_text = "Source nomi yoki organization bo'yicha qidiring."
    autocomplete_fields = ("center",)


@admin.register(Note)
class NoteAdmin(FriendlyAdminMixin):
    list_display = ("id", "lead", "operator", "short_text", "date")
    list_filter = ("operator", "date")
    search_fields = ("lead__phone_number", "lead__full_name", "text")
    search_help_text = "Izoh, lid yoki operator bo'yicha qidiring."
    autocomplete_fields = ("lead", "operator")
    date_hierarchy = "date"

    @admin.display(description="Izoh")
    def short_text(self, obj):
        text = obj.text or ""
        return text if len(text) <= 60 else f"{text[:57]}..."
