from django.apps import apps as django_apps
from django.contrib import admin, messages
from django.contrib.admin.sites import AlreadyRegistered
from django.db.models import Count

from apps.dashboard.admin_utils import FriendlyAdminMixin
from apps.teacher.models import Specialty, Teacher


@admin.register(Specialty)
class SpecialtyAdmin(FriendlyAdminMixin):
    list_display = ("id", "title")
    search_fields = ("title",)
    search_help_text = "Yo'nalishni nomi bo'yicha qidiring."


@admin.register(Teacher)
class TeacherAdmin(FriendlyAdminMixin):
    admin_page_title = "O'qituvchilar"
    admin_page_subtitle = "Ustozlar ro'yxati, biriktirilgan guruhlar va ish yuklamasini kuzating."
    change_list_template = "admin/teacher/teacher/change_list.html"
    list_display = (
        "id",
        "display_name",
        "phone_number",
        "branch",
        "assigned_groups_display",
        "specialties_list",
        "monthly_salary",
        "percentage_share",
        "is_archived",
    )
    list_filter = ("is_archived", "branch", "specialty", "contract_date", "created_at")
    search_fields = ("user__phone_number", "user__full_name", "branch__name", "specialty__title")
    search_help_text = "Teacher ni ism, telefon, filial yoki specialty bo'yicha qidiring."
    autocomplete_fields = ("user", "branch")
    filter_horizontal = ("specialty",)
    list_select_related = ("user", "branch")
    readonly_fields = ("created_at", "updated_at")
    actions = ("archive_selected_teachers", "restore_selected_teachers")
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("user", "branch", "image", "specialty", "is_archived"),
        }),
        ("Ish haqi va KPI", {
            "fields": ("monthly_salary", "kpi", "monthly_per_lesson", "monthly_per_student"),
        }),
        ("Shartnoma va ulush", {
            "fields": ("contract_date", "percentage_share", "lesson_fee", "per_student_fee"),
        }),
        ("Texnik ma'lumotlar", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user", "branch").prefetch_related(
            "specialty",
            "main_groups__course",
        ).annotate(group_count=Count("main_groups", distinct=True))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        queryset = self.get_queryset(request)
        extra_context.setdefault("teacher_page_metrics", {
            "total_teachers": queryset.count(),
            "active_teachers": queryset.filter(is_archived=False).count(),
            "busy_teachers": queryset.filter(group_count__gt=0).count(),
        })
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description="Teacher")
    def display_name(self, obj):
        if obj.user:
            return obj.user.display_name
        return f"Teacher #{obj.pk}"

    @admin.display(description="Telefon")
    def phone_number(self, obj):
        if obj.user:
            return obj.user.phone_number
        return None

    @admin.display(description="Yo'nalishlar")
    def specialties_list(self, obj):
        specialties = list(obj.specialty.all())
        titles = [item.title for item in specialties[:3]]
        if not titles:
            return "-"
        text = ", ".join(titles)
        if len(specialties) > 3:
            return f"{text}..."
        return text

    @admin.display(description="Biriktirilgan guruhlar")
    def assigned_groups_display(self, obj):
        count = getattr(obj, "group_count", None)
        if count is None:
            count = obj.main_groups.count()
        return count

    @admin.action(description="Tanlangan teacherlarni arxivga o'tkazish")
    def archive_selected_teachers(self, request, queryset):
        updated = queryset.update(is_archived=True)
        self.message_user(request, f"{updated} ta teacher arxivga o'tkazildi.", level=messages.SUCCESS)

    @admin.action(description="Tanlangan teacherlarni arxivdan chiqarish")
    def restore_selected_teachers(self, request, queryset):
        updated = queryset.update(is_archived=False)
        self.message_user(request, f"{updated} ta teacher qayta faollashtirildi.", level=messages.SUCCESS)


def _register_all_models():
    app_config = django_apps.get_app_config("teacher")
    for model in app_config.get_models():
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            pass


_register_all_models()
