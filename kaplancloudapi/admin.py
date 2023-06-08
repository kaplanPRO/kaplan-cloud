from django.contrib import admin

from kaplancloudapi.models import ProjectWebHook, ProjectFileWebHook

admin.site.register(ProjectWebHook)

admin.site.register(ProjectFileWebHook)
