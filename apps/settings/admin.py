from django.contrib import admin

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
