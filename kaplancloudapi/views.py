from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from kaplancloudapp.models import (
  Client, LanguageProfile, Project, ProjectFile,
  ProjectReferenceFile, TranslationMemory
)
from kaplancloudapi.models import ProjectFileWebHook, ProjectWebHook
from kaplancloudapi.serializers import (
  ClientSerializer, GroupSerializer, LanguageProfileSerializer, ProjectFileWebHookSerializer,
  ProjectSerializer, ProjectFileSerializer, ProjectReferenceFileSerializer, ProjectWebHookSerializer,
  TranslationMemorySerializer, UserSerializer
)


class ClientViewSet(viewsets.ModelViewSet):
  queryset = Client.objects.all()
  serializer_class = ClientSerializer
  filter_backends = (SearchFilter,)
  search_fields = ('name','team_member_username')

  def filter_queryset(self, queryset):
    queryset = super().filter_queryset(queryset)

    client_name = self.request.query_params.get('name', None)

    if client_name is not None:
      queryset = queryset.filter(name=client_name)

    team_member_username = self.request.query_params.get('team_member_username', None)

    if team_member_username is not None:
      queryset = queryset.filter(team=get_user_model().objects.get(username=team_member_username))

    return queryset


class GroupViewSet(viewsets.ModelViewSet):
  queryset = Group.objects.all()
  serializer_class = GroupSerializer


class LanguageProfileViewSet(viewsets.ModelViewSet):
  queryset = LanguageProfile.objects.all()
  serializer_class = LanguageProfileSerializer


class ProjectViewSet(viewsets.ModelViewSet):
  queryset = Project.objects.all()
  serializer_class = ProjectSerializer
  filter_backends = (SearchFilter,)
  search_fields = ('source_language', 'target_language', 'client_name')

  def filter_queryset(self, queryset):
    queryset = super().filter_queryset(queryset)

    client_name = self.request.query_params.get('client_name', None)
    
    if client_name is not None:
      queryset = queryset.filter(client=Client.objects.get(name=client_name))

    source_language = self.request.query_params.get('source_language', None)

    if source_language is not None:
      queryset = queryset.filter(source_language=source_language)

    target_language = self.request.query_params.get('target_language', None)

    if target_language is not None:
      queryset = queryset.filter(target_language=target_language)

    return queryset


class ProjectWebHookViewSet(viewsets.ModelViewSet):
  queryset = ProjectWebHook.objects.all()
  serializer_class = ProjectWebHookSerializer


class ProjectFileViewSet(viewsets.ModelViewSet):
  queryset = ProjectFile.objects.all()
  serializer_class = ProjectFileSerializer
  filter_backends = (SearchFilter,)
  search_fields = ('project_id')

  def filter_queryset(self, queryset):
    queryset = super().filter_queryset(queryset)

    project_id = self.request.query_params.get('project_id', None)
    
    if project_id is not None:
      queryset = queryset.filter(project=Project.objects.get(id=project_id))

    return queryset


class ProjectFileWebHookViewSet(viewsets.ModelViewSet):
  queryset = ProjectFileWebHook.objects.all()
  serializer_class = ProjectFileWebHookSerializer

  
class ProjectReferenceFileViewSet(viewsets.ModelViewSet):
  queryset = ProjectReferenceFile.objects.all()
  serializer_class = ProjectReferenceFileSerializer


class TranslationMemoryViewSet(viewsets.ModelViewSet):
  queryset = TranslationMemory.objects.all()
  serializer_class = TranslationMemorySerializer
  filter_backends = (SearchFilter,)
  search_fields = ('source_language', 'target_language', 'client_name')

  def filter_queryset(self, queryset):
    queryset = super().filter_queryset(queryset)

    client_name = self.request.query_params.get('client_name', None)
    
    if client_name is not None:
      queryset = queryset.filter(client=Client.objects.get(name=client_name))

    source_language = self.request.query_params.get('source_language', None)

    if source_language is not None:
      queryset = queryset.filter(source_language=source_language)

    target_language = self.request.query_params.get('target_language', None)

    if target_language is not None:
      queryset = queryset.filter(target_language=target_language)

    return queryset
  

class UserViewSet(viewsets.ModelViewSet):
  queryset = get_user_model().objects.all()
  serializer_class = UserSerializer
  filter_backends = (SearchFilter,)
  search_fields = ('username','client_name')

  def filter_queryset(self, queryset):
    queryset = super().filter_queryset(queryset)

    client_name = self.request.query_params.get('client_name', None)
    
    if client_name is not None:
      queryset = queryset.filter(id__in=Client.objects.get(name=client_name).team)

    username = self.request.query_params.get('username', None)

    if username is not None:
      queryset = queryset.filter(username=username)

    return queryset
