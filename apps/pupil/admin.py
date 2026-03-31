from django.apps import apps as django_apps
from django.contrib import admin, messages
from django.contrib.admin.sites import AlreadyRegistered

from apps.dashboard.admin_utils import FriendlyAdminMixin
from apps.pupil.choices import STUDENT_STATUS
from apps.pupil.coin import calculate_student_coin_offset, recalculate_student_total_coin
from apps.pupil.models import Parent, Student, StudentNote
from apps.pupil.models.student import StudnetTransfer


class CoinBalanceFilter(admin.SimpleListFilter):
    title = "Coin holati"
    parameter_name = "coin_balance"

    def lookups(self, request, model_admin):
        return (
            ("has_coin", "Coin bor"),
            ("zero_coin", "Coin yo'q"),
            ("used_coin", "Ishlatilgan coin bor"),
        )

    def queryset(self, request, queryset):
        if self.value() == "has_coin":
            return queryset.filter(total_coin__gt=0)
        if self.value() == "zero_coin":
            return queryset.filter(total_coin=0)
        if self.value() == "used_coin":
            return queryset.filter(used_coin__gt=0)
        return queryset


class LinkedAccountFilter(admin.SimpleListFilter):
    title = "Login account"
    parameter_name = "has_user"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Bor"),
            ("no", "Yo'q"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(user__isnull=False)
        if self.value() == "no":
            return queryset.filter(user__isnull=True)
        return queryset


class ParentInline(admin.TabularInline):
    model = Parent
    extra = 0
    fields = ("name", "phone_number")


class StudentNoteInline(admin.TabularInline):
    model = StudentNote
    extra = 0
    fields = ("text", "operator", "date")
    autocomplete_fields = ("operator",)


@admin.register(Student)
class StudentAdmin(FriendlyAdminMixin):
    list_display = (
        "id",
        "full_name",
        "phone_number",
        "center",
        "group",
        "status",
        "payment_status",
        "contract",
        "available_coin_display",
        "used_coin",
        "created_at",
    )
    list_filter = (
        CoinBalanceFilter,
        LinkedAccountFilter,
        "status",
        "payment_status",
        "contract",
        "center",
        "group",
        "created_at",
    )
    search_fields = (
        "full_name",
        "phone_number",
        "user__phone_number",
        "user__full_name",
        "group__title",
        "center__name",
    )
    search_help_text = "Talabani ism, telefon, guruh yoki markaz nomi bo'yicha qidiring."
    autocomplete_fields = ("user", "lead", "group", "center")
    list_select_related = ("user", "group", "center", "lead")
    readonly_fields = (
        "created_at",
        "updated_at",
        "available_coin_display",
        "earned_coin_display",
    )
    date_hierarchy = "created_at"
    actions = ("recalculate_coin_balance_action", "archive_students", "activate_students")
    inlines = (ParentInline, StudentNoteInline)
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("full_name", "phone_number", "user", "lead", "image", "comment"),
        }),
        ("O'qish holati", {
            "fields": ("center", "group", "status", "contract"),
        }),
        ("To'lov va coin", {
            "fields": (
                "payment_status",
                "next_payment_date",
                "balance",
                "used_coin",
                "total_coin",
                "available_coin_display",
                "earned_coin_display",
            ),
        }),
        ("Texnik ma'lumotlar", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.display(description="Mavjud coin", ordering="total_coin")
    def available_coin_display(self, obj):
        return obj.total_coin or 0

    @admin.display(description="Jami yig'ilgan coin")
    def earned_coin_display(self, obj):
        return obj.earned_coin

    def save_model(self, request, obj, form, change):
        desired_total_coin = form.cleaned_data.get("total_coin")

        super().save_model(request, obj, form, change)

        if desired_total_coin is not None and "total_coin" in getattr(form, "changed_data", []):
            obj.coin_offset = calculate_student_coin_offset(obj.pk, desired_total_coin)
            Student.objects.filter(pk=obj.pk).update(
                coin_offset=obj.coin_offset,
                total_coin=desired_total_coin,
            )
            obj.total_coin = desired_total_coin

    @admin.action(description="Tanlangan talabalar coin balansini qayta hisoblash")
    def recalculate_coin_balance_action(self, request, queryset):
        updated = 0
        for student_id in queryset.values_list("id", flat=True):
            recalculate_student_total_coin(student_id)
            updated += 1
        self.message_user(request, f"{updated} ta talabaning coin balansi yangilandi.", level=messages.SUCCESS)

    @admin.action(description="Tanlangan talabalarni arxivga o'tkazish")
    def archive_students(self, request, queryset):
        updated = queryset.update(status=STUDENT_STATUS.ARCHIVED)
        self.message_user(request, f"{updated} ta talaba arxivga o'tkazildi.", level=messages.SUCCESS)

    @admin.action(description="Tanlangan talabalarni active holatga qaytarish")
    def activate_students(self, request, queryset):
        updated = queryset.update(status=STUDENT_STATUS.ACTIVE)
        self.message_user(request, f"{updated} ta talaba active holatga qaytdi.", level=messages.SUCCESS)


@admin.register(Parent)
class ParentAdmin(FriendlyAdminMixin):
    list_display = ("id", "name", "phone_number", "student")
    search_fields = ("name", "phone_number", "student__full_name", "student__phone_number")
    search_help_text = "Parent yoki student bo'yicha qidiring."
    autocomplete_fields = ("student",)


@admin.register(StudentNote)
class StudentNoteAdmin(FriendlyAdminMixin):
    list_display = ("id", "student", "operator", "short_text", "date")
    list_filter = ("operator", "date")
    search_fields = ("student__full_name", "student__phone_number", "text")
    search_help_text = "Izoh matni yoki student bo'yicha qidiring."
    autocomplete_fields = ("student", "operator")
    date_hierarchy = "date"

    @admin.display(description="Izoh")
    def short_text(self, obj):
        text = obj.text or ""
        return text if len(text) <= 60 else f"{text[:57]}..."


@admin.register(StudnetTransfer)
class StudentTransferAdmin(FriendlyAdminMixin):
    list_display = (
        "id",
        "student",
        "from_group",
        "to_group",
        "from_branch",
        "to_branch",
        "reason_choice",
        "is_apply_discount",
        "is_debt",
    )
    list_filter = ("reason_choice", "is_apply_discount", "is_debt", "from_branch", "to_branch")
    search_fields = (
        "student__full_name",
        "student__phone_number",
        "from_group__title",
        "to_group__title",
        "reason",
    )
    search_help_text = "Student, guruh yoki sabab bo'yicha qidiring."
    autocomplete_fields = ("student", "from_group", "to_group", "from_branch", "to_branch")


def _register_all_models():
    app_config = django_apps.get_app_config("pupil")
    for model in app_config.get_models():
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            pass


_register_all_models()
