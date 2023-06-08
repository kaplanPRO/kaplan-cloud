from django.db.models.signals import post_save
from django.dispatch import receiver

from kaplancloudapi.models import ProjectWebHook, ProjectFileWebHook
from kaplancloudapp.models import Project, ProjectFile

@receiver(post_save, sender=Project)
def on_project_saved(sender, instance, **kwargs):
    for project_webhook in ProjectWebHook.objects.filter(project=instance):
        project_webhook.fire_hook()

@receiver(post_save, sender=ProjectFile)
def on_project_file_saved(sender, instance, **kwargs):
    for project_file_webhook in ProjectFileWebHook.objects.filter(project_file=instance):
        project_file_webhook.fire_hook()