from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Client, LanguageProfile, TranslationMemory

from datetime import datetime
from io import BytesIO
from pathlib import Path

from lxml import etree

from kaplan import open_bilingualfile
from kaplan.kxliff import KXLIFF


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

        tmp_dir = settings.BASE_DIR / 'kaplancloudapp' / '.tmp'
        if not tmp_dir.is_dir():
            tmp_dir.mkdir()

        validationerrors = []
        for i, file in enumerate(files):
            path_to_file = tmp_dir / (datetime.now().isoformat() + Path(file.name).suffix)

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

                path_to_file.unlink()

        if validationerrors != []:
            raise ValidationError(validationerrors)

        return files


class SearchForm(forms.Form):
    source = forms.ModelChoiceField(queryset=LanguageProfile.objects.all(), to_field_name='iso_code', required=False)
    target = forms.ModelChoiceField(queryset=LanguageProfile.objects.all(), to_field_name='iso_code', required=False)
    client = forms.ModelChoiceField(queryset=Client.objects.all(), required=False)


class TranslationMemoryForm(forms.Form):
    name = forms.CharField(max_length=64)
    source_language = forms.ModelChoiceField(queryset=LanguageProfile.objects.all(), to_field_name='iso_code', help_text='If you don\'t see the language you need, please create a LanguageProfile in the Admin dashboard.')
    target_language = forms.ModelChoiceField(queryset=LanguageProfile.objects.all(), to_field_name='iso_code', help_text='If you don\'t see the language you need, please create a LanguageProfile in the Admin dashboard.')
