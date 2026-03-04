from django.contrib import admin

from apps.lead.models import Lead, Situation, Note, Source
from apps.lead.services import assign_for_new_lead


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0
    fields = ("text", "operator", "date")
    # autocomplete_fields = ("operator",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone_number",
        "center",
        "status",
        "operator",
        "course",
        "group",
        "is_active",
        "is_archived",
        "created_at",
    )
    list_filter = ("status", "is_active", "is_archived", "center", "course")
    search_fields = ("full_name", "phone_number")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("center", "course", "operator", "group")
    # autocomplete_fields = ("course", "operator", "group", "center", "source", "situation")
    inlines = (NoteInline,)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            assign_for_new_lead(obj)


@admin.register(Situation)
class SituationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "organization", "is_static")
    list_filter = ("is_static", "organization")
    search_fields = ("title",)
    # autocomplete_fields = ("organization",)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "center", "is_static")
    list_filter = ("is_static", "center")
    search_fields = ("name",)
    # autocomplete_fields = ("center",)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("id", "lead", "operator", "date")
    list_filter = ("operator",)
    search_fields = ("lead__phone_number", "lead__full_name", "text")
    # autocomplete_fields = ("lead", "operator")
