from django.urls import path

from . import views

urlpatterns = [
    path('', views.projects, name='projects'),
    path('project/<int:id>', views.project, name='project'),
    path('file/<int:id>', views.editor, name='editor'),
    path('reference-file/<int:id>', views.reference_file, name='reference-file'),
    path('report/<int:id>', views.report, name='report'),
    path('project/new', views.newproject, name='newproject'),
    path('translation-memories', views.translation_memories, name='translation-memories'),
    path('translation-memory/<int:id>', views.translation_memory, name='tm'),
    path('translation-memory/<int:id>/import', views.translation_memory_import, name='tm-import'),
    path('translation-memory/new', views.newtm, name='newtm'),
]
