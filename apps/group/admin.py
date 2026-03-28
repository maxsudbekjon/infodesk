from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from apps.group.models import CourseTemplate, Day, Room, Group, Attendance, Grade, GroupScore


@admin.register(CourseTemplate)
class CourseTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "duration_months",
        "center",
        "created_at",
    )

    search_fields = (
        "name",
        "center__name",
    )

    list_filter = (
        "center",
        "created_at",
    )

    ordering = ("-created_at",)

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "day",
    )

    search_fields = ("day",)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "branch",
        "capacity",
        "created_at",
    )

    list_filter = (
        "branch",
    )

    search_fields = (
        "name",
        "branch__name",
    )

    # autocomplete_fields = (
    #     "branch",
    # )

    ordering = ("-created_at",)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "course",
        "branch",
        "teacher",
        "status",
        "start_lesson",
        "end_lesson",
        "total_student",
        "created_at",
    )

    list_filter = (
        "status",
        "branch",
        "course",
        "teacher",
        "lessons_days_choice",
    )

    search_fields = (
        "title",
        "teacher__user__first_name",
        "teacher__user__last_name",
        "course__name",
    )

    # autocomplete_fields = (
    #     "course",
    #     "branch",
    #     "teacher",
    #     "assistant_teacher",
    #     "room",
    # )

    filter_horizontal = (
        "lessons_days",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "student",
        "date",
        "is_present",
        "note",
    )

    search_fields = (
        "student__name",
        "group__title",
    )

    list_filter = (
        "is_present",
        "date",
        "group",
    )

    ordering = ("-date",)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "student",
        "date",
        "grade",
        "note",
    )

    search_fields = (
        "student__full_name",
        "group__title",
    )

    list_filter = (
        "date",
        "group",
    )

    ordering = ("-date",)


@admin.register(GroupScore)
class GroupScoreAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "student",
        "score",
        "reason",
        "created_at",
    )

    search_fields = (
        "student__full_name",
        "group__title",
        "reason",
    )

    list_filter = (
        "group",
        "created_at",
    )

    ordering = ("-created_at",)


def _register_all_models():
    app_config = django_apps.get_app_config("group")
    for model in app_config.get_models():
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            pass


_register_all_models()
