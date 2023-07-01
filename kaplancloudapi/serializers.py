from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password

from rest_framework import serializers

from kaplancloudapi.models import ProjectWebHook, ProjectFileWebHook

from kaplancloudapp.models import (
  Client, LanguageProfile, Project, ProjectFile,
  ProjectReferenceFile, TranslationMemory, file_statuses, project_statuses
)


class ClientSerializer(serializers.ModelSerializer):
  class Meta:
    model = Client
    fields = ('id', 'name', 'team')


class GroupSerializer(serializers.ModelSerializer):
  id = serializers.ReadOnlyField()
  
  class Meta:
    model = Group
    fields = '__all__'


class LanguageProfileSerializer(serializers.ModelSerializer):
  is_ltr = serializers.BooleanField(default=True, initial=True)

  class Meta:
    model = LanguageProfile
    fields = ('name', 'iso_code', 'is_ltr')
  
  def create(self, validated_data):
    validated_data['created_by'] = self.context['request'].user

    return super().create(validated_data)


class ProjectSerializer(serializers.ModelSerializer):
  status = serializers.ChoiceField(choices=project_statuses, default=0, initial=0)

  class Meta:
    model = Project
    fields = (
      'id', 'uuid', 'name', 'source_language', 'target_language', 'client',
      'managed_by', 'status', 'translationmemories', 'due_by', '_are_all_files_submitted',
    )

  def create(self, validated_data):
    validated_data['created_by'] = self.context['request'].user

    return super().create(validated_data)


class ProjectWebHookSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProjectWebHook
    fields = '__all__'


class ProjectFileSerializer(serializers.ModelSerializer):
  status = serializers.ChoiceField(choices=file_statuses, default=0, initial=0)
  
  class Meta:
    model = ProjectFile
    exclude = ('bilingual_file',)


class ProjectFileWebHookSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProjectFileWebHook
    fields = '__all__'


class ProjectReferenceFileSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProjectReferenceFile
    fields = ('id', 'uuid', 'name', 'reference_file', 'project')


class TranslationMemorySerializer(serializers.ModelSerializer):
  class Meta:
    model = TranslationMemory
    fields = ('id', 'uuid', 'name', 'source_language', 'target_language', 'client')

  def create(self, validated_data):
    validated_data['created_by'] = self.context['request'].user

    return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
  is_active = serializers.BooleanField(initial=True)

  class Meta:
    model = get_user_model()
    fields = ('id', 'username', 'password', 'email', 'is_active', 'groups')

  def create(self, validated_data):
    validated_data['password'] = make_password(validated_data.get('password'))

    return super().create(validated_data)
