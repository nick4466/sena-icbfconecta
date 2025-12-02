from django.apps import AppConfig


class PlaneacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planeaciones'

    def ready(self):
        import planeaciones.signals