from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from .models import (
    Branch,
    Organization,
    PaymentMethod,
    ReceiptSettings,
    Weekend,
)


admin.site.register(Organization)
admin.site.register(Branch)
admin.site.register(ReceiptSettings)
admin.site.register(PaymentMethod)
admin.site.register(Weekend)


def _register_all_models():
    app_config = django_apps.get_app_config("settings")
    for model in app_config.get_models():
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            pass


_register_all_models()
