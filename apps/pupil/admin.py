import calendar
from collections import defaultdict
from datetime import date

from django import forms
from django.apps import apps as django_apps
from django.contrib import admin, messages
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.admin.utils import unquote
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from apps.dashboard.admin_utils import FriendlyAdminMixin
from apps.pupil.choices import STUDENT_PAYMENT, STUDENT_STATUS
from apps.pupil.coin import calculate_student_coin_offset, recalculate_student_total_coin
from apps.pupil.models import Parent, Student, StudentNote
from apps.pupil.models.student import StudentTransfer
from apps.group.models import Attendance, GroupScore
from apps.group.utils import get_student_groups_queryset


class StudentAdminForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=[*Student._meta.get_field("status").choices, ("active", "Faol")],
        required=False,
    )
    add_coin = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=150,
        label="Coin qo'shish",
        help_text="Bir martada ko'pi bilan 150 coin qo'shish mumkin.",
    )
    remove_coin = forms.IntegerField(
        required=False,
        min_value=0,
        label="Coin ayirish",
        help_text="Istalgan miqdorda coin ayirish mumkin.",
    )

    class Meta:
        model = Student
        fields = "__all__"

    def clean_status(self):
        status = self.cleaned_data.get("status")
        if status == "active":
            return STUDENT_STATUS.ACTIVE
        return status

    def clean(self):
        cleaned_data = super().clean()
        add_coin = int(cleaned_data.get("add_coin") or 0)
        remove_coin = int(cleaned_data.get("remove_coin") or 0)

        if (add_coin or remove_coin) and "total_coin" in self.changed_data:
            self.add_error(
                "total_coin",
                "Coin qo'shish yoki ayirish ishlatilganda jami coin maydonini alohida o'zgartirmang.",
            )

        return cleaned_data


class ParentInlineForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = "__all__"
        labels = {
            "name": "F.I.Sh",
            "phone_number": "Telefon",
            "student": "O'quvchi",
        }


class StudentNoteInlineForm(forms.ModelForm):
    class Meta:
        model = StudentNote
        fields = "__all__"
        labels = {
            "text": "Matn",
            "operator": "Operator",
            "date": "Sana",
            "student": "O'quvchi",
        }


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
    title = "Login hisobi"
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
    form = ParentInlineForm
    extra = 0
    fields = ("name", "phone_number")
    verbose_name = "Ota-ona"
    verbose_name_plural = "Ota-onalar"


class StudentNoteInline(admin.TabularInline):
    model = StudentNote
    form = StudentNoteInlineForm
    extra = 0
    fields = ("text", "operator", "date")
    autocomplete_fields = ("operator",)
    verbose_name = "Izoh"
    verbose_name_plural = "Izohlar"


@admin.register(Student)
class StudentAdmin(FriendlyAdminMixin):
    form = StudentAdminForm
    admin_page_title = "O'quvchilar"
    admin_page_subtitle = "Talabalarni jadval, holat va to'lov kesimida tez boshqaring."
    change_list_template = "admin/pupil/student/change_list.html"
    list_display = (
        "id",
        "full_name",
        "phone_number",
        "center",
        "group",
        "status_badge",
        "payment_status_badge",
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
                "add_coin",
                "remove_coin",
                "available_coin_display",
                "earned_coin_display",
            ),
        }),
        ("Texnik ma'lumotlar", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/attendance/",
                self.admin_site.admin_view(self.attendance_view),
                name="pupil_student_attendance",
            ),
            path(
                "<path:object_id>/coin/update/",
                self.admin_site.admin_view(self.quick_coin_update_view),
                name="pupil_student_coin_update",
            ),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        queryset = self.get_queryset(request)
        extra_context.setdefault("student_page_metrics", {
            "total_students": queryset.count(),
            "active_students": queryset.filter(status=STUDENT_STATUS.ACTIVE).count(),
            "inactive_students": queryset.exclude(status=STUDENT_STATUS.ACTIVE).count(),
            "debtor_students": queryset.filter(payment_status=STUDENT_PAYMENT.DEBTOR).count(),
        })
        return super().changelist_view(request, extra_context=extra_context)

    def attendance_view(self, request, object_id):
        student = self.get_object(request, unquote(object_id))
        if student is None:
            raise Http404("O'quvchi topilmadi.")
        if not self.has_view_or_change_permission(request, student):
            raise Http404("O'quvchini ko'rish huquqi yo'q.")

        month = request.GET.get("month")
        year = request.GET.get("year")
        today = timezone.localdate()
        try:
            month = int(month or today.month)
            year = int(year or today.year)
        except (TypeError, ValueError):
            month = today.month
            year = today.year

        month = min(max(month, 1), 12)
        days = list(range(1, calendar.monthrange(year, month)[1] + 1))
        student_groups = list(
            get_student_groups_queryset(student)
            .select_related("course", "teacher__user", "branch")
            .order_by("title")
        )
        group_ids = [group.id for group in student_groups]

        attendance_map = defaultdict(dict)
        attendances = Attendance.objects.filter(
            student=student,
            group_id__in=group_ids,
            date__year=year,
            date__month=month,
        ).select_related("group")
        for attendance in attendances:
            attendance_map[attendance.group_id][attendance.date.day] = attendance

        coin_totals = {
            row["group_id"]: row["total_coin"] or 0
            for row in GroupScore.objects.filter(
                student=student,
                group_id__in=group_ids,
                created_at__year=year,
                created_at__month=month,
            )
            .values("group_id")
            .annotate(total_coin=Coalesce(Sum("score"), 0))
        }

        group_rows = []
        present_total = absent_total = unmarked_total = 0
        for group in student_groups:
            present_count = absent_count = unmarked_count = 0
            cells = []
            for day in days:
                attendance = attendance_map.get(group.id, {}).get(day)
                if attendance is None:
                    tone = "neutral"
                    label = "-"
                    short = ""
                    unmarked_count += 1
                elif attendance.is_present is True:
                    tone = "present"
                    label = "Kelgan"
                    short = "K"
                    present_count += 1
                elif attendance.is_present is False:
                    tone = "absent"
                    label = "Kelmagan"
                    short = "Y"
                    absent_count += 1
                else:
                    tone = "neutral"
                    label = "Belgilanmagan"
                    short = ""
                    unmarked_count += 1

                cells.append({
                    "day": day,
                    "date_iso": date(year, month, day).isoformat(),
                    "tone": tone,
                    "state": tone,
                    "label": label,
                    "short": short,
                })

            present_total += present_count
            absent_total += absent_count
            unmarked_total += unmarked_count
            group_rows.append({
                "group": group,
                "teacher_name": (
                    group.teacher.user.display_name
                    if group.teacher_id and group.teacher and group.teacher.user
                    else "Biriktirilmagan"
                ),
                "coin": int(student.total_coin or 0),
                "monthly_coin": coin_totals.get(group.id, 0),
                "present_count": present_count,
                "absent_count": absent_count,
                "unmarked_count": unmarked_count,
                "cells": cells,
            })

        prev_month = month - 1 or 12
        prev_year = year - 1 if month == 1 else year
        next_month = month + 1 if month < 12 else 1
        next_year = year + 1 if month == 12 else year

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": student,
            "title": f"{student.full_name or student.phone_number} davomat",
            "subtitle": "Bir oylik umumiy davomat va coin ko'rinishi.",
            "student_attendance": {
                "student": student,
                "days": days,
                "month": month,
                "year": year,
                "group_rows": group_rows,
                "summary": {
                    "present_total": present_total,
                    "absent_total": absent_total,
                    "unmarked_total": unmarked_total,
                    "coin_total": int(student.total_coin or 0),
                    "group_total": len(group_rows),
                },
                "prev_query": f"month={prev_month}&year={prev_year}",
                "next_query": f"month={next_month}&year={next_year}",
            },
            "attendance_update_url": reverse("admin:group_attendance_update"),
            "change_url": reverse("admin:pupil_student_change", args=[student.pk]),
            "back_url": reverse("admin:pupil_student_changelist"),
        }
        return TemplateResponse(request, "admin/pupil/student/attendance.html", context)

    @admin.display(description="Mavjud coin", ordering="total_coin")
    def available_coin_display(self, obj):
        return obj.total_coin or 0

    @admin.display(description="Jami yig'ilgan coin")
    def earned_coin_display(self, obj):
        return obj.earned_coin

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        palette = {
            STUDENT_STATUS.ACTIVE: ("Aktiv", "success"),
            STUDENT_STATUS.FROZEN: ("To'xtatilgan", "warning"),
            STUDENT_STATUS.ARCHIVED: ("Arxiv", "muted"),
            STUDENT_STATUS.LEAD: ("Lead", "info"),
        }
        label, tone = palette.get(obj.status, (obj.get_status_display(), "info"))
        return format_html('<span class="status-badge status-badge--{}">{}</span>', tone, label)

    @admin.display(description="To'lov", ordering="payment_status")
    def payment_status_badge(self, obj):
        palette = {
            "near payment": ("Yaqin to'lov", "warning"),
            "debtor": ("Qarzdor", "danger"),
            "no debt": ("To'langan", "success"),
            "over payment": ("Ortiqcha to'lov", "info"),
        }
        label, tone = palette.get(obj.payment_status, (obj.get_payment_status_display(), "info"))
        return format_html('<span class="status-badge status-badge--{}">{}</span>', tone, label)

    def _set_student_total_coin(self, student, target_total_coin: int) -> Student:
        target_total_coin = max(int(target_total_coin or 0), 0)
        student.coin_offset = calculate_student_coin_offset(student.pk, target_total_coin)
        Student.objects.filter(pk=student.pk).update(
            coin_offset=student.coin_offset,
            total_coin=target_total_coin,
        )
        student.total_coin = target_total_coin
        return student

    def quick_coin_update_view(self, request, object_id):
        if request.method != "POST":
            return HttpResponseBadRequest("Faqat POST so'rovi qabul qilinadi.")

        student = self.get_object(request, unquote(object_id))
        if student is None:
            raise Http404("O'quvchi topilmadi.")
        if not self.has_change_permission(request, student):
            return HttpResponseBadRequest("O'quvchini o'zgartirishga ruxsat yo'q.")

        action = (request.POST.get("action") or "").strip()
        try:
            amount = int(request.POST.get("amount") or 0)
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "error": "Coin miqdorini son ko'rinishida kiriting."}, status=400)

        if action not in {"add", "remove"}:
            return JsonResponse({"ok": False, "error": "Noto'g'ri amal turi yuborildi."}, status=400)
        if amount <= 0:
            return JsonResponse({"ok": False, "error": "Coin miqdori 0 dan katta bo'lishi kerak."}, status=400)
        if action == "add" and amount > 150:
            return JsonResponse({"ok": False, "error": "Bir martada ko'pi bilan 150 coin qo'shish mumkin."}, status=400)

        current_total = int(student.total_coin or 0)
        target_total = current_total + amount if action == "add" else max(current_total - amount, 0)
        self._set_student_total_coin(student, target_total)

        return JsonResponse(
            {
                "ok": True,
                "student_id": student.pk,
                "total_coin": int(student.total_coin or 0),
                "action": action,
                "amount": amount,
            }
        )

    def save_model(self, request, obj, form, change):
        previous_total_coin = 0
        if change and obj.pk:
            previous_total_coin = (
                Student.objects.filter(pk=obj.pk).values_list("total_coin", flat=True).first() or 0
            )

        desired_total_coin = form.cleaned_data.get("total_coin")
        add_coin = int(form.cleaned_data.get("add_coin") or 0)
        remove_coin = int(form.cleaned_data.get("remove_coin") or 0)

        super().save_model(request, obj, form, change)

        target_total_coin = None
        if add_coin or remove_coin:
            base_total_coin = previous_total_coin if change else int(obj.total_coin or 0)
            target_total_coin = max(base_total_coin + add_coin - remove_coin, 0)
        elif desired_total_coin is not None and "total_coin" in getattr(form, "changed_data", []):
            target_total_coin = int(desired_total_coin)

        if target_total_coin is not None:
            self._set_student_total_coin(obj, target_total_coin)

        if add_coin or remove_coin:
            parts = []
            if add_coin:
                parts.append(f"+{add_coin}")
            if remove_coin:
                parts.append(f"-{remove_coin}")
            self.message_user(
                request,
                f"{obj.full_name or obj.phone_number} uchun coin yangilandi: {' '.join(parts)}. Hozirgi balans {obj.total_coin}.",
                level=messages.SUCCESS,
            )

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


@admin.register(StudentTransfer)
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
