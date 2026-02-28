from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from apps.group.models import CourseTemplate, Day, Room, Group


admin.site.register(CourseTemplate)
admin.site.register(Day)
admin.site.register(Room)
admin.site.register(Group)


def _register_all_models():
    app_config = django_apps.get_app_config("group")
    for model in app_config.get_models():
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            pass


_register_all_models()
