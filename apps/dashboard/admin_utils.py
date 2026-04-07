from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.contrib import admin


MODAL_REQUEST_PARAM = "_ui_modal"
MODAL_UPDATED_PARAM = "_modal_updated"


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
        if not self.is_modal_request(request) or not getattr(response, "url", None):
            return response

        params = {self.modal_request_param: 1}
        if close_modal:
            params[self.modal_updated_param] = 1

        response.url = append_query_params(response.url, **params)
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


class FriendlyAdminMixin(AdminUiResponseMixin, admin.ModelAdmin):
    list_per_page = 25
    save_on_top = True
    show_full_result_count = True
    show_facets = admin.ShowFacets.ALWAYS
    empty_value_display = "-"
