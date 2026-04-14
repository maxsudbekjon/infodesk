from __future__ import annotations

from collections import OrderedDict
from datetime import date, timedelta

from django.contrib.admin.models import LogEntry
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone

from apps.group.choices import GROUP_STATUS
from apps.group.models import CourseTemplate, Group
from apps.lead.choices import LEAD_STATUS
from apps.lead.models import Lead
from apps.market.models import MARKET_ORDER_STATUS, MarketOrder
from apps.pupil.choices import STUDENT_PAYMENT, STUDENT_STATUS
from apps.pupil.models import Student
from apps.teacher.models import Teacher


def _user_display_name(user) -> str:
    return getattr(user, "display_name", None) or getattr(user, "get_username", lambda: "")() or "Foydalanuvchi"


def _teacher_name(teacher: Teacher | None) -> str:
    if not teacher:
        return "Biriktirilmagan"
    if teacher.user:
        return teacher.user.display_name
    return f"Ustoz #{teacher.pk}"


def _group_schedule(group: Group) -> str:
    day_names = [day.day for day in group.lessons_days.all()]
    if day_names:
        day_text = ", ".join(day_names)
    else:
        day_text = group.get_lessons_days_choice_display() or "Jadval kiritilmagan"
    return f"{day_text} · {group.start_lesson:%H:%M} - {group.end_lesson:%H:%M}"


def _active_match(request_path: str, target_url: str) -> bool:
    if request_path == target_url:
        return True
    if target_url != reverse("admin:index") and request_path.startswith(target_url):
        return True
    return False


def _shift_month(reference: date, offset: int) -> date:
    total_months = reference.year * 12 + reference.month - 1 + offset
    year, month_index = divmod(total_months, 12)
    return date(year, month_index + 1, 1)


def _month_label(value: date) -> str:
    labels = {
        1: "Yan",
        2: "Fev",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Iyn",
        7: "Iyl",
        8: "Avg",
        9: "Sen",
        10: "Okt",
        11: "Noy",
        12: "Dek",
    }
    return labels.get(value.month, value.strftime("%b"))


def _monthly_overview(queryset, *, label: str, color: str, months: int = 6):
    current_month = timezone.localdate().replace(day=1)
    month_starts = [
        _shift_month(current_month, -offset)
        for offset in range(months - 1, -1, -1)
    ]

    aggregated = (
        queryset.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    counts = {
        date(row["month"].year, row["month"].month, 1): row["total"]
        for row in aggregated
        if row["month"]
    }

    peak = max(counts.values(), default=0)
    items = []
    for month_start in month_starts:
        total = counts.get(month_start, 0)
        items.append({
            "label": _month_label(month_start),
            "value": total,
            "height": 18 if peak == 0 else max(round(total / peak * 100, 2), 18),
        })

    current_total = items[-1]["value"] if items else 0
    previous_total = items[-2]["value"] if len(items) > 1 else 0
    delta = current_total - previous_total
    if delta > 0:
        change_text = f"+{delta} o'tgan oyga nisbatan"
        change_tone = "success"
    elif delta < 0:
        change_text = f"{delta} o'tgan oyga nisbatan"
        change_tone = "danger"
    else:
        change_text = "O'tgan oy bilan bir xil"
        change_tone = "muted"

    return {
        "label": label,
        "color": color,
        "items": items,
        "current": current_total,
        "change_text": change_text,
        "change_tone": change_tone,
    }


def _build_dashboard_quick_links(request):
    items = [
        {
            "title": "Guruhlar",
            "description": "Kartochka ko'rinishida guruhlar, ustoz va jadvalni boshqaring.",
            "icon": "groups",
            "url": reverse("admin:group_group_changelist"),
            "visible": request.user.has_perm("group.view_group"),
        },
        {
            "title": "O'quvchilar",
            "description": "Qidiruv, filtr va status badge bilan talabalarni kuzating.",
            "icon": "students",
            "url": reverse("admin:pupil_student_changelist"),
            "visible": request.user.has_perm("pupil.view_student"),
        },
        {
            "title": "Buyurtmalar",
            "description": "Yangi leadlarni ko'rib chiqing va qabul qilish jarayonini tezlashtiring.",
            "icon": "orders",
            "url": reverse("admin:lead_lead_changelist"),
            "visible": request.user.has_perm("lead.view_lead"),
        },
        {
            "title": "Jadval",
            "description": "Dars kunlari, vaqt va auditoriyalarni bitta toza sahifada ko'ring.",
            "icon": "calendar",
            "url": reverse("admin:ui_schedule"),
            "visible": request.user.has_perm("group.view_group"),
        },
        {
            "title": "Statistika",
            "description": "Markaz bo'yicha asosiy ko'rsatkichlar va holat breakdown’larini ko'ring.",
            "icon": "stats",
            "url": reverse("admin:ui_statistics"),
            "visible": True,
        },
    ]
    return [item for item in items if item["visible"]]


def _build_notifications(request):
    notifications = []

    if request.user.has_perm("lead.view_lead"):
        new_leads = Lead.objects.filter(status=LEAD_STATUS.NEW, is_archived=False).count()
        notifications.append({
            "label": "Yangi buyurtmalar",
            "value": new_leads,
            "description": "Ko'rib chiqilmagan leadlar soni",
            "tone": "primary",
            "url": reverse("admin:lead_lead_changelist"),
        })

    if request.user.has_perm("pupil.view_student"):
        debtors = Student.objects.filter(payment_status=STUDENT_PAYMENT.DEBTOR).count()
        notifications.append({
            "label": "Qarzdor o'quvchilar",
            "value": debtors,
            "description": "To'lov holati e'tibor talab qiladi",
            "tone": "danger",
            "url": reverse("admin:pupil_student_changelist"),
        })

    if request.user.has_perm("market.view_marketorder"):
        market_orders = MarketOrder.objects.filter(status=MARKET_ORDER_STATUS.CREATED).count()
        notifications.append({
            "label": "Market buyurtmalari",
            "value": market_orders,
            "description": "Yangi market orderlar",
            "tone": "success",
            "url": reverse("admin:market_marketorder_changelist"),
        })

    return notifications


def _build_global_metrics(request):
    metrics = []

    if request.user.has_perm("pupil.view_student"):
        total_students = Student.objects.count()
        active_students = Student.objects.filter(status=STUDENT_STATUS.ACTIVE).count()
        metrics.extend([
            {
                "label": "Jami o'quvchilar",
                "value": total_students,
                "icon": "students",
                "tone": "primary",
                "helper": "Barcha ro'yxatdan o'tgan talabalar",
            },
            {
                "label": "Aktiv o'quvchilar",
                "value": active_students,
                "icon": "pulse",
                "tone": "success",
                "helper": "Hozir o'qishda davom etayotganlar",
            },
        ])

    if request.user.has_perm("group.view_group"):
        metrics.append({
            "label": "Guruhlar soni",
            "value": Group.objects.count(),
            "icon": "groups",
            "tone": "info",
            "helper": "Faol va arxiv guruhlar jami",
        })

    if request.user.has_perm("lead.view_lead"):
        metrics.append({
            "label": "Yangi buyurtmalar",
            "value": Lead.objects.filter(status=LEAD_STATUS.NEW, is_archived=False).count(),
            "icon": "orders",
            "tone": "warning",
            "helper": "Qayta aloqa kutayotgan leadlar",
        })

    return metrics


def _build_dashboard_trends(request):
    trends = []

    if request.user.has_perm("pupil.view_student"):
        trends.append(
            _monthly_overview(
                Student.objects.all(),
                label="O'quvchilar oqimi",
                color="#3B82F6",
            )
        )

    if request.user.has_perm("group.view_group"):
        trends.append(
            _monthly_overview(
                Group.objects.all(),
                label="Yangi guruhlar",
                color="#10B981",
            )
        )

    if request.user.has_perm("lead.view_lead"):
        trends.append(
            _monthly_overview(
                Lead.objects.all(),
                label="Kelgan buyurtmalar",
                color="#F59E0B",
            )
        )

    return trends


def _build_dashboard_snapshot(request):
    snapshot = {
        "recent_groups": [],
        "recent_students": [],
        "recent_leads": [],
        "recent_actions": [],
    }

    if request.user.has_perm("group.view_group"):
        groups = (
            Group.objects.select_related("course", "branch", "teacher__user")
            .prefetch_related("lessons_days")
            .annotate(student_count=Count("students", distinct=True))
            .order_by("-created_at")[:4]
        )
        snapshot["recent_groups"] = [
            {
                "title": group.title,
                "teacher": _teacher_name(group.teacher),
                "subject": getattr(group.course, "name", "-"),
                "students": group.student_count or group.total_student,
                "schedule": _group_schedule(group),
                "url": reverse("admin:group_group_change", args=[group.pk]),
            }
            for group in groups
        ]

    if request.user.has_perm("pupil.view_student"):
        students = (
            Student.objects.select_related("group", "center")
            .order_by("-created_at")[:4]
        )
        snapshot["recent_students"] = [
            {
                "name": student.full_name or student.phone_number or f"Student #{student.pk}",
                "phone": student.phone_number or "-",
                "group": getattr(student.group, "title", "Guruhsiz"),
                "status": student.get_status_display(),
                "url": reverse("admin:pupil_student_change", args=[student.pk]),
            }
            for student in students
        ]

    if request.user.has_perm("lead.view_lead"):
        leads = (
            Lead.objects.select_related("course", "operator__user")
            .order_by("-created_at")[:4]
        )
        status_labels = dict(Lead._meta.get_field("status").choices)
        snapshot["recent_leads"] = [
            {
                "name": lead.full_name,
                "phone": lead.phone_number,
                "status": status_labels.get(lead.status, lead.status),
                "course": getattr(lead.course, "name", "-"),
                "url": reverse("admin:lead_lead_change", args=[lead.pk]),
            }
            for lead in leads
        ]

    recent_actions = LogEntry.objects.select_related("content_type", "user").order_by("-action_time")[:5]
    snapshot["recent_actions"] = [
        {
            "label": entry.object_repr,
            "actor": _user_display_name(entry.user),
            "content_type": entry.content_type.name if entry.content_type else "Noma'lum obyekt",
            "time": timezone.localtime(entry.action_time),
            "url": entry.get_admin_url(),
        }
        for entry in recent_actions
    ]
    return snapshot


def _choice_breakdown(queryset, field_name, choices, palette):
    counts = OrderedDict((value, 0) for value, _ in choices)
    for row in queryset.values(field_name).annotate(total=Count("id")).order_by():
        counts[row[field_name]] = row["total"]

    max_value = max(counts.values()) if counts else 0
    items = []
    for index, (value, label) in enumerate(choices):
        total = counts.get(value, 0)
        width = 0 if max_value == 0 else round(total / max_value * 100, 2)
        items.append({
            "label": label,
            "value": total,
            "width": width,
            "color": palette[index % len(palette)],
        })
    return items


def dashboard_callback(request, context):
    """Unfold dashboard callback — adds dashboard data to the index page context."""
    notifications = _build_notifications(request)
    context.update({
        "admin_dashboard_quick_links": _build_dashboard_quick_links(request),
        "admin_notifications": notifications,
        "admin_notification_total": sum(item["value"] for item in notifications),
        "admin_global_metrics": _build_global_metrics(request),
        "admin_dashboard_snapshot": _build_dashboard_snapshot(request),
        "admin_dashboard_trends": _build_dashboard_trends(request),
        "admin_search_url": reverse("admin:ui_global_search"),
        "admin_schedule_url": reverse("admin:ui_schedule"),
        "admin_statistics_url": reverse("admin:ui_statistics"),
    })
    return context


def ui_global_search_view(request):
    query = (request.GET.get("q") or "").strip()
    if len(query) < 2:
        return JsonResponse({"results": []})

    results = []

    if request.user.has_perm("pupil.view_student"):
        students = (
            Student.objects.select_related("group")
            .filter(
                Q(full_name__icontains=query)
                | Q(phone_number__icontains=query)
                | Q(group__title__icontains=query)
            )
            .distinct()[:4]
        )
        for student in students:
            results.append({
                "category": "O'quvchilar",
                "title": student.full_name or student.phone_number or f"Student #{student.pk}",
                "meta": f"{student.phone_number or '-'} · {getattr(student.group, 'title', 'Guruhsiz')}",
                "url": reverse("admin:pupil_student_change", args=[student.pk]),
                "icon": "students",
            })

    if request.user.has_perm("group.view_group"):
        groups = (
            Group.objects.select_related("course", "teacher__user")
            .filter(
                Q(title__icontains=query)
                | Q(course__name__icontains=query)
                | Q(teacher__user__full_name__icontains=query)
                | Q(teacher__user__phone_number__icontains=query)
            )
            .distinct()[:4]
        )
        for group in groups:
            results.append({
                "category": "Guruhlar",
                "title": group.title,
                "meta": f"{getattr(group.course, 'name', '-')} · {_teacher_name(group.teacher)}",
                "url": reverse("admin:group_group_change", args=[group.pk]),
                "icon": "groups",
            })

    if request.user.has_perm("teacher.view_teacher"):
        teachers = (
            Teacher.objects.select_related("user", "branch")
            .filter(
                Q(user__full_name__icontains=query)
                | Q(user__phone_number__icontains=query)
                | Q(branch__name__icontains=query)
            )
            .distinct()[:4]
        )
        for teacher in teachers:
            results.append({
                "category": "O'qituvchilar",
                "title": _teacher_name(teacher),
                "meta": f"{getattr(getattr(teacher, 'branch', None), 'name', 'Filial kiritilmagan')}",
                "url": reverse("admin:teacher_teacher_change", args=[teacher.pk]),
                "icon": "teachers",
            })

    if request.user.has_perm("group.view_coursetemplate"):
        subjects = (
            CourseTemplate.objects.select_related("center")
            .filter(Q(name__icontains=query) | Q(center__name__icontains=query))
            .distinct()[:3]
        )
        for subject in subjects:
            results.append({
                "category": "Fanlar",
                "title": subject.name,
                "meta": f"{getattr(subject.center, 'name', '-')} · {subject.duration_months} oy",
                "url": reverse("admin:group_coursetemplate_change", args=[subject.pk]),
                "icon": "subjects",
            })

    if request.user.has_perm("lead.view_lead"):
        leads = (
            Lead.objects.select_related("course")
            .filter(
                Q(full_name__icontains=query)
                | Q(phone_number__icontains=query)
                | Q(course__name__icontains=query)
            )
            .distinct()[:4]
        )
        lead_statuses = dict(Lead._meta.get_field("status").choices)
        for lead in leads:
            results.append({
                "category": "Buyurtmalar",
                "title": lead.full_name,
                "meta": f"{lead.phone_number} · {lead_statuses.get(lead.status, lead.status)}",
                "url": reverse("admin:lead_lead_change", args=[lead.pk]),
                "icon": "orders",
            })

    if request.user.has_perm("market.view_marketorder"):
        orders = (
            MarketOrder.objects.select_related("student", "product")
            .filter(
                Q(secret_code__icontains=query)
                | Q(student__full_name__icontains=query)
                | Q(student__phone_number__icontains=query)
                | Q(product__title__icontains=query)
            )
            .distinct()[:3]
        )
        for order in orders:
            results.append({
                "category": "Market",
                "title": order.secret_code,
                "meta": f"{order.student} · {order.product}",
                "url": reverse("admin:market_marketorder_change", args=[order.pk]),
                "icon": "market",
            })

    return JsonResponse({"results": results[:15]})


def ui_statistics_view(request, admin_site):
    palette = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#6366F1", "#14B8A6"]
    context = {
        **admin_site.each_context(request),
        "title": "Statistika",
        "subtitle": "O'quv markazi bo'yicha asosiy holat va yuklamalarni kuzating.",
        "student_status_breakdown": _choice_breakdown(
            Student.objects.all(),
            "status",
            Student._meta.get_field("status").choices,
            palette,
        ),
        "group_status_breakdown": _choice_breakdown(
            Group.objects.all(),
            "status",
            Group._meta.get_field("status").choices,
            palette,
        ),
        "lead_status_breakdown": _choice_breakdown(
            Lead.objects.all(),
            "status",
            Lead._meta.get_field("status").choices,
            palette,
        ),
        "teacher_summary": {
            "total": Teacher.objects.count(),
            "archived": Teacher.objects.filter(is_archived=True).count(),
            "active": Teacher.objects.filter(is_archived=False).count(),
        },
        "upcoming_payments": Student.objects.filter(
            next_payment_date__isnull=False,
            next_payment_date__lte=timezone.localdate() + timedelta(days=7),
        ).count(),
        "active_groups": Group.objects.filter(status=GROUP_STATUS.ACTIVE).count(),
        "new_leads": Lead.objects.filter(status=LEAD_STATUS.NEW, is_archived=False).count(),
        "top_subjects": CourseTemplate.objects.annotate(
            group_total=Count("groups", distinct=True),
            lead_total=Count("leads", distinct=True),
        ).order_by("-group_total", "-lead_total", "name")[:5],
        "teacher_workloads": Teacher.objects.select_related("user").annotate(
            group_total=Count("main_groups", distinct=True),
        ).order_by("-group_total", "user__full_name")[:5],
    }
    return TemplateResponse(request, "admin/statistics.html", context)


def ui_schedule_view(request, admin_site):
    teacher_id = request.GET.get("teacher")
    subject_id = request.GET.get("subject")

    groups = (
        Group.objects.select_related("course", "teacher__user", "branch", "room")
        .prefetch_related("lessons_days")
        .annotate(student_count=Count("students", distinct=True))
        .order_by("start_lesson", "title")
    )

    if teacher_id:
        groups = groups.filter(teacher_id=teacher_id)
    if subject_id:
        groups = groups.filter(course_id=subject_id)

    schedule_summary = {
        "total_groups": groups.count(),
        "total_teachers": groups.exclude(teacher__isnull=True).values("teacher").distinct().count(),
        "total_subjects": groups.values("course").distinct().count(),
        "total_students": groups.aggregate(total_students=Sum("student_count")).get("total_students") or 0,
    }

    context = {
        **admin_site.each_context(request),
        "title": "Jadval",
        "subtitle": "Dars kunlari, vaqt va guruh yuklamalarini yagona jadvalda ko'ring.",
        "schedule_groups": groups,
        "schedule_summary": schedule_summary,
        "schedule_teachers": Teacher.objects.select_related("user").order_by("user__full_name"),
        "schedule_subjects": CourseTemplate.objects.order_by("name"),
        "selected_teacher": teacher_id or "",
        "selected_subject": subject_id or "",
    }
    return TemplateResponse(request, "admin/schedule.html", context)
