from django.apps import AppConfig

class DeyirmanAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'deyirman_app'

    def ready(self):
        from . import signals
