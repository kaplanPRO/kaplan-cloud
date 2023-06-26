from django.contrib.auth.models import Group, User
from django.contrib.auth.hashers import make_password

from rest_framework import serializers

from kaplancloudapi.models import ProjectWebHook, ProjectFileWebHook

from kaplancloudapp.models import (
  Client, LanguageProfile, Project, ProjectFile,
  ProjectReferenceFile, TranslationMemory
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
    fields = ('id', 'name', 'iso_code', 'is_ltr')
  
  def create(self, validated_data):
    validated_data['created_by'] = self.context['request'].user

    return super().create(validated_data)


class ProjectSerializer(serializers.ModelSerializer):
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
  class Meta:
    model = ProjectFile
    exclude = ('bilingual_file', 'source_language', 'target_language')


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
    model = User
    fields = ('id', 'username', 'password', 'email', 'is_active', 'groups')

  def create(self, validated_data):
    validated_data['password'] = make_password(validated_data.get('password'))

    return super().create(validated_data)