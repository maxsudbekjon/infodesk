from django.apps import AppConfig


class GroupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.group'

    def ready(self):
        import apps.group.signals  # noqa: F401
