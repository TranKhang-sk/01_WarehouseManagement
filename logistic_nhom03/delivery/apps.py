from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'delivery'
    def ready(self):
        from .scheduler import start_scheduler
        start_scheduler()