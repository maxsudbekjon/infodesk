from django.contrib import admin

from .models import (
    Branch,
    CourseTemplate,
    Organization,
    PaymentMethod,
    ReceiptSettings,
    Weekend,
)


admin.site.register(Organization)
admin.site.register(Branch)
admin.site.register(ReceiptSettings)
admin.site.register(PaymentMethod)
admin.site.register(CourseTemplate)
admin.site.register(Weekend)
