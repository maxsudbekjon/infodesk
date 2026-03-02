from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from apps.lead.models import Lead, Situation, Note
from apps.lead.services import assign_for_new_lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            assign_for_new_lead(obj)


admin.site.register(Situation)
admin.site.register(Note)


def _register_all_models():
    app_config = django_apps.get_app_config("lead")
    for model in app_config.get_models():
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            pass


_register_all_models()
