import calendar
import json
from collections import defaultdict
from datetime import date

from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.admin.utils import unquote
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone

from apps.dashboard.admin_utils import FriendlyAdminMixin
from apps.group.choices import GROUP_STATUS
from apps.group.models import Attendance, CourseTemplate, Day, Grade, Group, GroupScore, Room
from apps.group.utils import get_group_students


@admin.register(CourseTemplate)
class CourseTemplateAdmin(FriendlyAdminMixin):
    admin_page_title = "Fanlar"
    admin_page_subtitle = "Yo'nalishlar, narx va davomiylikni bir joydan boshqaring."
    change_list_template = "admin/group/coursetemplate/change_list.html"
    list_display = ("id", "name", "price", "duration_months", "center", "groups_count_display", "created_at")
    search_fields = ("name", "center__name")
    search_help_text = "Kurs nomi yoki organization bo'yicha qidiring."
    list_filter = ("center", "created_at")
    list_select_related = ("center",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("center").annotate(groups_count=Count("groups", distinct=True))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        queryset = self.get_queryset(request)
        extra_context.setdefault("subject_page_metrics", {
            "total_subjects": queryset.count(),
            "total_groups": sum(subject.groups_count for subject in queryset),
        })
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description="Guruhlar")
    def groups_count_display(self, obj):
        return getattr(obj, "groups_count", 0)


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
    admin_page_title = "Guruhlar"
    admin_page_subtitle = "Jadval, ustoz va o'quvchilar kesimida guruhlarni boshqaring."
    change_list_template = "admin/group/group/change_list.html"
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

    def get_urls(self):
        custom_urls = [
            path(
                "attendance/update/",
                self.admin_site.admin_view(self.attendance_update_view),
                name="group_attendance_update",
            ),
            path(
                "<path:object_id>/overview/",
                self.admin_site.admin_view(self.overview_view),
                name="group_group_overview",
            ),
        ]
        return custom_urls + super().get_urls()

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "course",
            "branch",
            "teacher__user",
            "assistant_teacher__user",
            "room",
        ).prefetch_related("lessons_days").annotate(student_count=Count("students", distinct=True))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        queryset = self.get_queryset(request)
        extra_context.setdefault("group_page_metrics", {
            "total_groups": queryset.count(),
            "active_groups": queryset.filter(status=GROUP_STATUS.ACTIVE).count(),
            "archived_groups": queryset.filter(status=GROUP_STATUS.ARCHIVED).count(),
        })
        return super().changelist_view(request, extra_context=extra_context)

    def overview_view(self, request, object_id):
        group = (
            self.get_queryset(request)
            .filter(pk=unquote(object_id))
            .first()
        )
        if group is None:
            raise Http404("Guruh topilmadi.")
        if not self.has_view_or_change_permission(request, group):
            raise Http404("Guruhni ko'rish huquqi yo'q.")

        today = timezone.localdate()
        try:
            month = int(request.GET.get("month") or today.month)
            year = int(request.GET.get("year") or today.year)
        except (TypeError, ValueError):
            month = today.month
            year = today.year

        month = min(max(month, 1), 12)
        days = list(range(1, calendar.monthrange(year, month)[1] + 1))
        students = get_group_students(group)
        student_ids = [student.id for student in students]

        attendance_map = defaultdict(dict)
        attendances = Attendance.objects.filter(
            group=group,
            student_id__in=student_ids,
            date__year=year,
            date__month=month,
        )
        for attendance in attendances:
            attendance_map[attendance.student_id][attendance.date.day] = attendance

        coin_totals = {
            row["student_id"]: row["total_coin"] or 0
            for row in GroupScore.objects.filter(
                group=group,
                student_id__in=student_ids,
                created_at__year=year,
                created_at__month=month,
            )
            .values("student_id")
            .annotate(total_coin=Coalesce(Sum("score"), 0))
        }

        rows = []
        present_total = absent_total = unmarked_total = 0
        for student in students:
            present_count = absent_count = unmarked_count = 0
            cells = []
            for day in days:
                attendance = attendance_map.get(student.id, {}).get(day)
                if attendance is None:
                    tone = "neutral"
                    short = ""
                    label = "-"
                    unmarked_count += 1
                elif attendance.is_present is True:
                    tone = "present"
                    short = "K"
                    label = "Kelgan"
                    present_count += 1
                elif attendance.is_present is False:
                    tone = "absent"
                    short = "Y"
                    label = "Kelmagan"
                    absent_count += 1
                else:
                    tone = "neutral"
                    short = ""
                    label = "Belgilanmagan"
                    unmarked_count += 1

                cells.append({
                    "day": day,
                    "date_iso": date(year, month, day).isoformat(),
                    "tone": tone,
                    "state": tone,
                    "short": short,
                    "label": label,
                })

            present_total += present_count
            absent_total += absent_count
            unmarked_total += unmarked_count
            rows.append({
                "student": student,
                "coin": int(student.total_coin or 0),
                "monthly_coin": coin_totals.get(student.id, 0),
                "present_count": present_count,
                "absent_count": absent_count,
                "unmarked_count": unmarked_count,
                "cells": cells,
                "attendance_url": reverse("admin:pupil_student_attendance", args=[student.pk]),
                "change_url": reverse("admin:pupil_student_change", args=[student.pk]),
            })

        prev_month = month - 1 or 12
        prev_year = year - 1 if month == 1 else year
        next_month = month + 1 if month < 12 else 1
        next_year = year + 1 if month == 12 else year

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": group,
            "title": f"{group.title} davomat",
            "subtitle": "Guruhdagi o'quvchilar ro'yxati va bir oylik umumiy davomat.",
            "group_overview": {
                "group": group,
                "days": days,
                "month": month,
                "year": year,
                "rows": rows,
                "summary": {
                    "student_total": len(students),
                    "present_total": present_total,
                    "absent_total": absent_total,
                    "coin_total": sum(int(row["coin"] or 0) for row in rows),
                },
                "prev_query": f"month={prev_month}&year={prev_year}",
                "next_query": f"month={next_month}&year={next_year}",
            },
            "attendance_update_url": reverse("admin:group_attendance_update"),
            "change_url": reverse("admin:group_group_change", args=[group.pk]),
            "back_url": reverse("admin:group_group_changelist"),
        }
        return TemplateResponse(request, "admin/group/group/overview.html", context)

    def attendance_update_view(self, request):
        if request.method != "POST":
            return HttpResponseBadRequest("POST required.")

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (TypeError, ValueError, json.JSONDecodeError):
            return HttpResponseBadRequest("Invalid JSON payload.")

        group_id = payload.get("group_id")
        student_id = payload.get("student_id")
        date_value = payload.get("date")
        state = payload.get("state")

        if state not in {"present", "absent", "neutral"}:
            return HttpResponseBadRequest("Invalid attendance state.")

        if not group_id or not student_id or not date_value:
            return HttpResponseBadRequest("Missing attendance identifiers.")

        try:
            attendance_date = date.fromisoformat(str(date_value))
        except ValueError:
            return HttpResponseBadRequest("Invalid attendance date.")

        try:
            student_id = int(student_id)
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Invalid student identifier.")

        group = Group.objects.filter(pk=group_id).first()
        student = None
        if group is not None:
            student = next(
                (item for item in get_group_students(group) if item.pk == student_id),
                None,
            )
        if group is None or student is None:
            return HttpResponseBadRequest("Student or group not found.")

        is_present = {
            "present": True,
            "absent": False,
            "neutral": None,
        }[state]

        attendance, _ = Attendance.objects.update_or_create(
            group=group,
            student=student,
            date=attendance_date,
            defaults={"is_present": is_present},
        )

        return JsonResponse(
            {
                "ok": True,
                "attendance_id": attendance.pk,
                "state": state,
                "label": {
                    "present": "Kelgan",
                    "absent": "Kelmagan",
                    "neutral": "Belgilanmagan yoki dars yo'q",
                }[state],
            }
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
