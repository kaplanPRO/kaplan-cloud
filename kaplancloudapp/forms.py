from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Client, LanguageProfile, TranslationMemory

from datetime import datetime
from io import BytesIO
from pathlib import Path
import tempfile

from lxml import etree

from kaplan import open_bilingualfile
from kaplan.kxliff import KXLIFF


class AssignLinguistForm(forms.Form):
    username = forms.CharField(max_length=128)
    override = forms.BooleanField(required=False)
    role = forms.ChoiceField(choices=((0,'Translator'),(1,'Reviewer')), initial=0, widget=forms.HiddenInput())
    file_ids = forms.CharField(widget=forms.HiddenInput())

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
            return username
        except User.DoesNotExist:
            raise ValidationError('No users found with that username')


class KPPUploadForm(forms.Form):
    package = forms.FileField(widget=forms.ClearableFileInput(attrs={'accept': ','.join(['.kpp', '.krpp'])}))


class ProjectForm(forms.Form):
    name = forms.CharField(max_length=64)
    source_language = forms.ModelChoiceField(queryset=LanguageProfile.objects.all(), to_field_name='iso_code', help_text='If you don\'t see the language you need, please create a LanguageProfile in the Admin dashboard.')
    target_language = forms.ModelChoiceField(queryset=LanguageProfile.objects.all(), to_field_name='iso_code', help_text='If you don\'t see the language you need, please create a LanguageProfile in the Admin dashboard.')
    translation_memories = forms.ChoiceField(required=False)
    client = forms.ModelChoiceField(queryset=Client.objects.all(), required=False)
    project_files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True, 'accept': ','.join(['.docx', '.kxliff', '.odp', '.ods', '.odt', '.po', '.sdlxliff', '.txt', '.xliff'])}))
    reference_files = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'multiple':True}))
    due_by = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

    def clean_target_language(self):
        source_language = self.cleaned_data['source_language'].iso_code
        target_language = self.cleaned_data['target_language'].iso_code
        if source_language == target_language:
            raise ValidationError('Source and target language cannot be the same.')

        return self.cleaned_data['target_language']

    def clean_translation_memories(self):
        if self.cleaned_data['translation_memories'] != '' and self.cleaned_data['translation_memories'] != '-----':
            tm = TranslationMemory.objects.get(id=self.cleaned_data['translation_memories'])
            if (tm.source_language != self.cleaned_data['source_language'].iso_code
            or tm.target_language != self.cleaned_data['target_language'].iso_code):
                raise ValidationError('TM language pair is different from that of the project.')
            else:
                return [tm]
        else:
            return []

    def clean_project_files(self):
        files = self.files.getlist('project_files')

        validationerrors = []
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for i, file in enumerate(files):
                path_to_file = tmpdir_path / file.name

                with open(path_to_file, 'wb') as f:
                    f.write(file.read())

                try:
                    open_bilingualfile(str(path_to_file))
                    files[i].name = 'BF-' + file.name
                except:
                    try:
                        KXLIFF.new(str(path_to_file), 'xx', 'xx')
                        files[i].name = 'MF-' + file.name
                    except:
                        validationerrors.append(ValidationError('{0} not compatible.'.format(file.name)))

        if validationerrors != []:
            raise ValidationError(validationerrors)

        return files


class SearchForm(forms.Form):
    source = forms.ModelChoiceField(queryset=LanguageProfile.objects.all(), to_field_name='iso_code', required=False)
    target = forms.ModelChoiceField(queryset=LanguageProfile.objects.all(), to_field_name='iso_code', required=False)
    client = forms.ModelChoiceField(queryset=Client.objects.all(), required=False)


class SegmentCommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea)


class TranslationMemoryForm(forms.Form):
    name = forms.CharField(max_length=64)
    source_language = forms.ModelChoiceField(queryset=LanguageProfile.objects.all(), to_field_name='iso_code', help_text='If you don\'t see the language you need, please create a LanguageProfile in the Admin dashboard.')
    target_language = forms.ModelChoiceField(queryset=LanguageProfile.objects.all(), to_field_name='iso_code', help_text='If you don\'t see the language you need, please create a LanguageProfile in the Admin dashboard.')
    client = forms.ModelChoiceField(queryset=Client.objects.all(), required=False)


class TranslationMemoryImportForm(forms.Form):
    source_language = forms.CharField(max_length=10, required=False, help_text='Language code')
    target_language = forms.CharField(max_length=10, required=False, help_text='Language code')
    tm_file = forms.FileField(label='TM file', widget=forms.ClearableFileInput(attrs={'accept': ','.join(['.kdb', '.tmx'])}))

    def clean_tm_file(self):
        tm_file = self.files['tm_file']

        if Path(tm_file.name).suffix.lower() not in ['.kdb', '.tmx']:
            raise ValidationError('This can only process .kdb or .tmx files.')

        return self.cleaned_data['tm_file']
