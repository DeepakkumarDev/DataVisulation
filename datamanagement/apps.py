from django.apps import AppConfig


class DatamanagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'datamanagement'


    def ready(self) -> None:
        # return super().ready()
        import datamanagement.signals.handlers