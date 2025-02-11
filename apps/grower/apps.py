from django.apps import AppConfig

class GrowerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.grower'

    def ready(self):
        import apps.grower.signals
