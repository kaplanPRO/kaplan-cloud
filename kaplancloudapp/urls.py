from django.urls import path

from . import views

urlpatterns = [
    path('', views.projects, name='projects'),
    path('project/<uuid:uuid>', views.project, name='project'),
    path('file/<uuid:uuid>', views.editor, name='editor'),
    path('reference-file/<uuid:uuid>', views.reference_file, name='reference-file'),
    path('report/<uuid:uuid>', views.report, name='report'),
    path('project/new', views.newproject, name='newproject'),
    path('translation-memories', views.translation_memories, name='translation-memories'),
    path('translation-memory/<uuid:uuid>', views.translation_memory, name='tm'),
    path('translation-memory/<uuid:uuid>/import', views.translation_memory_import, name='tm-import'),
    path('translation-memory/new', views.newtm, name='newtm'),
]
