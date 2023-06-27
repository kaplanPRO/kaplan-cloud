from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'clients', views.ClientViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'language-profiles', views.LanguageProfileViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'project-webhooks', views.ProjectWebHookViewSet)
router.register(r'project-files', views.ProjectFileViewSet)
router.register(r'project-file-webhooks', views.ProjectFileWebHookViewSet)
router.register(r'project-reference-files', views.ProjectReferenceFileViewSet)
router.register(r'translation-memories', views.TranslationMemoryViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]