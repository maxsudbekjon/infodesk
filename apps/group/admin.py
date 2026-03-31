from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from apps.dashboard.admin_utils import FriendlyAdminMixin
from apps.group.models import Attendance, CourseTemplate, Day, Grade, Group, GroupScore, Room


@admin.register(CourseTemplate)
class CourseTemplateAdmin(FriendlyAdminMixin):
    list_display = ("id", "name", "price", "duration_months", "center", "created_at")
    search_fields = ("name", "center__name")
    search_help_text = "Kurs nomi yoki organization bo'yicha qidiring."
    list_filter = ("center", "created_at")
    list_select_related = ("center",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Day)
class DayAdmin(FriendlyAdminMixin):
    list_display = ("id", "day")
    search_fields = ("day",)
    search_help_text = "Kun nomi bo'yicha qidiring."


@admin.register(Room)
class RoomAdmin(FriendlyAdminMixin):
    list_display = ("id", "name", "branch", "capacity", "created_at")
    list_filter = ("branch", "created_at")
    search_fields = ("name", "branch__name")
    search_help_text = "Xona yoki filial nomi bo'yicha qidiring."
    autocomplete_fields = ("branch",)
    list_select_related = ("branch",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Group)
class GroupAdmin(FriendlyAdminMixin):
    list_display = (
        "id",
        "title",
        "course",
        "branch",
        "teacher",
        "assistant_teacher",
        "status",
        "lesson_time",
        "total_student",
        "created_at",
    )
    list_filter = ("status", "branch", "course", "teacher", "assistant_teacher", "lessons_days_choice")
    search_fields = (
        "title",
        "course__name",
        "branch__name",
        "teacher__user__full_name",
        "teacher__user__phone_number",
        "assistant_teacher__user__full_name",
    )
    search_help_text = "Guruh nomi, kurs, filial yoki teacher bo'yicha qidiring."
    autocomplete_fields = ("course", "branch", "teacher", "assistant_teacher", "room", "students")
    filter_horizontal = ("lessons_days",)
    list_select_related = ("course", "branch", "teacher__user", "assistant_teacher__user", "room")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("title", "course", "branch", "status"),
        }),
        ("Teacher va xona", {
            "fields": ("teacher", "assistant_teacher", "room"),
        }),
        ("Jadval", {
            "fields": ("lessons_days_choice", "lessons_days", "start_lesson", "end_lesson", "started_at", "closed_at"),
        }),
        ("Talabalar", {
            "fields": ("students", "total_student"),
        }),
        ("Texnik ma'lumotlar", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.display(description="Dars vaqti")
    def lesson_time(self, obj):
        return f"{obj.start_lesson} - {obj.end_lesson}"


@admin.register(Attendance)
class AttendanceAdmin(FriendlyAdminMixin):
    list_display = ("id", "group", "student", "date", "is_present", "note")
    search_fields = ("student__full_name", "student__phone_number", "group__title")
    search_help_text = "Davomatni student yoki guruh bo'yicha qidiring."
    list_filter = ("is_present", "date", "group")
    autocomplete_fields = ("group", "student")
    list_select_related = ("group", "student")
    ordering = ("-date",)
    date_hierarchy = "date"


@admin.register(Grade)
class GradeAdmin(FriendlyAdminMixin):
    list_display = ("id", "group", "student", "date", "grade", "note")
    search_fields = ("student__full_name", "student__phone_number", "group__title")
    search_help_text = "Bahoni student yoki guruh bo'yicha qidiring."
    list_filter = ("date", "group")
    autocomplete_fields = ("group", "student")
    list_select_related = ("group", "student")
    ordering = ("-date",)
    date_hierarchy = "date"


@admin.register(GroupScore)
class GroupScoreAdmin(FriendlyAdminMixin):
    list_display = ("id", "group", "student", "score", "reason", "created_at")
    search_fields = ("student__full_name", "student__phone_number", "group__title", "reason")
    search_help_text = "Coin yozuvini student, guruh yoki sabab bo'yicha qidiring."
    list_filter = ("group", "created_at")
    autocomplete_fields = ("group", "student")
    list_select_related = ("group", "student")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


def _register_all_models():
    app_config = django_apps.get_app_config("group")
    for model in app_config.get_models():
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            pass


_register_all_models()
