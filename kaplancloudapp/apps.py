from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kaplancloudapp'

    def ready(self):
        from .signals import new_file_handler, segment_update_handler, tmentry_update_handler
