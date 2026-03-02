from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from apps.teacher.models import Specialty, Teacher


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'monthly_salary', 'kpi', 'monthly_per_lesson', 'monthly_per_student', 'is_archived')
    search_fields = ('user__phone_number',)
    list_filter = ('is_archived',)


def _register_all_models():
    app_config = django_apps.get_app_config("teacher")
    for model in app_config.get_models():
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            pass


_register_all_models()
