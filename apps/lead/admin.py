from django.contrib import admin
from apps.lead.models import Lead,Situation,Note
# Register your models here.
admin.site.register(Lead)
admin.site.register(Situation)
admin.site.register(Note)