from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db.models import NOT_PROVIDED
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import path, reverse
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline as UnfoldTabularInline


MODAL_REQUEST_PARAM = "_ui_modal"
MODAL_UPDATED_PARAM = "_modal_updated"

FIELD_LABEL_OVERRIDES = {
    "full_name": "F.I.Sh",
    "phone_number": "Telefon",
    "phone_number2": "Qo'shimcha telefon",
    "user": "Foydalanuvchi",
    "lead": "Lid",
    "image": "Rasm",
    "comment": "Izoh",
    "center": "Markaz",
    "group": "Guruh",
    "status": "Holat",
    "contract": "Shartnoma",
    "payment_status": "To'lov holati",
    "next_payment_date": "Keyingi to'lov sanasi",
    "balance": "Balans",
    "used_coin": "Ishlatilgan coin",
    "total_coin": "Jami coin",
    "created_at": "Yaratilgan vaqti",
    "updated_at": "Yangilangan vaqti",
    "teacher": "O'qituvchi",
    "assistant_teacher": "Yordamchi o'qituvchi",
    "room": "Xona",
    "branch": "Filial",
    "lessons_days_choice": "Dars kunlari",
    "lessons_days": "Dars kunlari tanlovi",
    "start_lesson": "Dars boshlanishi",
    "end_lesson": "Dars tugashi",
    "started_at": "Boshlangan sana",
    "closed_at": "Yakunlangan sana",
    "title": "Nomi",
    "name": "Nomi",
    "price": "Narxi",
    "duration_months": "Davomiyligi (oy)",
    "operator": "Operator",
    "source": "Manba",
    "situation": "Vaziyat",
    "temperature": "Qiziqish darajasi",
    "days_choice": "Kunlar turi",
    "days": "Kunlar",
    "prefer_time": "Qulay vaqt",
    "is_active": "Faol",
    "is_archived": "Arxivlangan",
    "monthly_salary": "Oylik maosh",
    "kpi": "KPI",
    "monthly_per_lesson": "Bir dars uchun to'lov",
    "monthly_per_student": "Bir o'quvchi uchun to'lov",
    "contract_date": "Shartnoma sanasi",
    "percentage_share": "Ulush foizi",
    "lesson_fee": "Dars narxi",
    "per_student_fee": "Bir o'quvchi narxi",
    "specialty": "Yo'nalish",
    "note": "Izoh",
    "date": "Sana",
    "reason": "Sabab",
    "reason_choice": "Sabab turi",
    "is_present": "Davomat",
    "capacity": "Sig'imi",
    "day": "Kun",
    "text": "Matn",
}


def append_query_params(url: str, **params) -> str:
    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    for key, value in params.items():
        if value is None:
            query.pop(key, None)
        else:
            query[key] = str(value)

    return urlunsplit(parsed._replace(query=urlencode(query, doseq=True)))


class AdminUiResponseMixin:
    admin_page_title = None
    admin_page_subtitle = None
    modal_request_param = MODAL_REQUEST_PARAM
    modal_updated_param = MODAL_UPDATED_PARAM

    def is_modal_request(self, request) -> bool:
        return (
            request.GET.get(self.modal_request_param) == "1"
            or request.POST.get(self.modal_request_param) == "1"
        )

    def _inject_admin_page_context(self, extra_context=None):
        extra_context = extra_context or {}
        if self.admin_page_title:
            extra_context.setdefault("title", self.admin_page_title)
        if self.admin_page_subtitle:
            extra_context.setdefault("subtitle", self.admin_page_subtitle)
        return extra_context

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(
            request,
            extra_context=self._inject_admin_page_context(extra_context),
        )

    def add_view(self, request, form_url="", extra_context=None):
        return super().add_view(
            request,
            form_url=form_url,
            extra_context=self._inject_admin_page_context(extra_context),
        )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return super().change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=self._inject_admin_page_context(extra_context),
        )

    def delete_view(self, request, object_id, extra_context=None):
        return super().delete_view(
            request,
            object_id,
            extra_context=self._inject_admin_page_context(extra_context),
        )

    def _preserve_modal_state(self, request, response, *, close_modal=False):
        if not self.is_modal_request(request):
            return response

        location = response.headers.get("Location") if hasattr(response, "headers") else None
        if not location:
            return response

        params = {self.modal_request_param: 1}
        if close_modal:
            params[self.modal_updated_param] = 1

        response["Location"] = append_query_params(location, **params)
        return response

    def response_add(self, request, obj, post_url_continue=None):
        response = super().response_add(request, obj, post_url_continue=post_url_continue)
        close_modal = "_continue" not in request.POST and "_addanother" not in request.POST
        return self._preserve_modal_state(request, response, close_modal=close_modal)

    def response_change(self, request, obj):
        response = super().response_change(request, obj)
        close_modal = "_continue" not in request.POST and "_addanother" not in request.POST
        return self._preserve_modal_state(request, response, close_modal=close_modal)

    def response_delete(self, request, obj_display, obj_id):
        response = super().response_delete(request, obj_display, obj_id)
        return self._preserve_modal_state(request, response, close_modal=True)

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/quick-delete/",
                self.admin_site.admin_view(self.quick_delete_view),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_quick_delete",
            ),
        ]
        return custom_urls + super().get_urls()

    def quick_delete_view(self, request, object_id):
        if request.method not in {"GET", "POST"}:
            return HttpResponseNotAllowed(["GET", "POST"])

        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            raise Http404(f"{self.model._meta.verbose_name} topilmadi.")
        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        object_label = str(obj)
        try:
            obj.delete()
        except ProtectedError:
            self.message_user(
                request,
                f"{object_label} ni o'chirib bo'lmadi: unga bog'langan himoyalangan yozuvlar mavjud.",
                level=messages.ERROR,
            )
        else:
            self.message_user(
                request,
                f"{self.model._meta.verbose_name.capitalize()} muvaffaqiyatli o'chirildi.",
                level=messages.SUCCESS,
            )

        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect(reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist"))


class FriendlyAdminMixin(AdminUiResponseMixin, UnfoldModelAdmin):
    list_per_page = 25
    save_on_top = True
    show_full_result_count = True
    show_facets = admin.ShowFacets.ALWAYS
    empty_value_display = "-"

    def get_form(self, request, obj=None, change=False, **kwargs):
        form_class = super().get_form(request, obj=obj, change=change, **kwargs)

        for field_name, form_field in form_class.base_fields.items():
            if field_name in FIELD_LABEL_OVERRIDES:
                form_field.label = FIELD_LABEL_OVERRIDES[field_name]

            try:
                model_field = self.model._meta.get_field(field_name)
            except Exception:
                continue

            if getattr(model_field, "default", NOT_PROVIDED) is NOT_PROVIDED:
                continue

            if form_field.required:
                form_field.required = False

            if form_field.initial in (None, ""):
                default_value = model_field.get_default()
                if default_value not in (None, ""):
                    form_field.initial = default_value

        return form_class
