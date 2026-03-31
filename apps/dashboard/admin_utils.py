from django.contrib import admin


class FriendlyAdminMixin(admin.ModelAdmin):
    list_per_page = 25
    save_on_top = True
    show_full_result_count = True
    show_facets = admin.ShowFacets.ALWAYS
    empty_value_display = "-"
