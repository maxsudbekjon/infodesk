from django.contrib import admin
from django.urls import path

from apps.dashboard.admin_ui import (
    build_admin_ui_context,
    ui_global_search_view,
    ui_schedule_view,
    ui_statistics_view,
)

admin.site.site_header = "Infodesk Boshqaruv Paneli"
admin.site.site_title = "Infodesk Admin"
admin.site.index_title = "Kerakli bo'limni tanlang"
admin.site.empty_value_display = "-"
admin.site.index_template = "admin/index.html"


if not getattr(admin.site, "_infodesk_ui_patched", False):
    original_each_context = admin.site.each_context
    original_get_urls = admin.site.get_urls

    def infodesk_each_context(request):
        context = original_each_context(request)
        context.update(build_admin_ui_context(request))
        return context

    def infodesk_get_urls():
        custom_urls = [
            path(
                "ui/search/",
                admin.site.admin_view(ui_global_search_view),
                name="ui_global_search",
            ),
            path(
                "schedule/",
                admin.site.admin_view(lambda request: ui_schedule_view(request, admin.site)),
                name="ui_schedule",
            ),
            path(
                "statistics/",
                admin.site.admin_view(lambda request: ui_statistics_view(request, admin.site)),
                name="ui_statistics",
            ),
        ]
        return custom_urls + original_get_urls()

    admin.site.each_context = infodesk_each_context
    admin.site.get_urls = infodesk_get_urls
    admin.site._infodesk_ui_patched = True
