from django.apps import AppConfig


class KaplancloudapiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kaplancloudapi'

    def ready(self):
        # Import the signal instances and connect them
        # from myapp.signals import my_signal
        import kaplancloudapi.signals