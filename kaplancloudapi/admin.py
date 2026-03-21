from django.contrib import admin

from kaplancloudapi.models import ProjectFileWebHook, ProjectWebHook

admin.site.register(ProjectWebHook)

admin.site.register(ProjectFileWebHook)
