from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.serializers import serialize
from django.http import FileResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect, render

from .forms import ProjectForm, TranslationMemoryForm
from .models import ProjectFile, Project, Segment, TranslationMemory, TMEntry

from datetime import datetime
from pathlib import Path

from lxml import etree
from kaplan import open_bilingualfile

# Create your views here.

@login_required
def newproject(request):
    form = ProjectForm(request.POST or None, request.FILES or None)
    form.fields['translation_memories'].choices = ((request.POST.get('translation_memories'),'-----'),)
    if form.is_valid():
        new_project = Project()
        new_project.name = form.cleaned_data['name']
        new_project.source_language = form.cleaned_data['source_language'].iso_code
        new_project.target_language = form.cleaned_data['target_language'].iso_code
        new_project.due_by = form.cleaned_data['due_by']
        new_project.created_by = request.user
        new_project.save()

        for tm in form.cleaned_data['translation_memories']:
            new_project.translationmemories.add(tm)
        new_project_directory = Path('./kaplancloudapp/projects') / str(new_project.created_by.id) / str(new_project.id)
        new_project_directory.mkdir(parents=True)
        new_project.directory = str(new_project_directory)
        new_project.save()

        for file in form.files.getlist('project_files'):
            new_file = ProjectFile()
            new_file.name = file.name[3:]
            new_file.source_language = new_project.source_language
            new_file.target_language = new_project.target_language
            new_file.project = new_project
            new_file_name = file.name[3:]
            if file.name[:3] == 'MF-':
                new_file.source_file.save(new_file_name, file)
            else:
                new_file.source_bilingualfile.save(new_file_name, file)
            new_file.save()

        return redirect('projects')

    return render(request, 'newproject.html', {'form':form})

@login_required
def newtm(request):
    form = TranslationMemoryForm(request.POST or None)

    if form.is_valid():
        tm = TranslationMemory()
        tm.name = form.cleaned_data['name']
        tm.source_language = form.cleaned_data['source_language'].iso_code
        tm.target_language = form.cleaned_data['target_language'].iso_code
        tm.user = request.user
        tm.save()

        return redirect('translation-memories')

    return render(request, 'newtm.html', {'form':form})

@login_required
def projects(request):
    projects = list(Project.objects.filter(created_by=request.user) | Project.objects.filter(managed_by=request.user))

    project_files = ProjectFile.objects.all()
    for project in projects:
        project_files = project_files.exclude(project=project)

    for project_file in project_files:
        if project_file.translator == request.user or project_file.reviewer == request.user:
            if project_file.project not in projects:
                projects.append(project_file.project)

    return render(request, 'projects.html', {'at_projects':True, 'projects':sorted(projects, key=lambda x: x.id, reverse=True)})

@login_required
def project(request, id):
    project = Project.objects.get(id=id)
    project_files = ProjectFile.objects.filter(project=project)
    if project.created_by != request.user and request.user not in project.managed_by.all():
        project_files = project_files.filter(translator=request.user) | project_files.filter(reviewer=request.user)
        if len(project_files) == 0:
            return redirect('/accounts/login?next={0}'.format(request.path))

    if request.method == 'POST':
        if request.POST.get('task') == 'download_translation':
            project_file = project_files.get(id=int(request.POST['file_id']))
            if project_file.source_file is not None:
                bf = open_bilingualfile(project_file.target_bilingualfile.path)
                bf.generate_target_translation(project_file.get_target_directory(), target_filename=project_file.name)
                return FileResponse(open(Path(project_file.get_target_directory()) / project_file.name, 'rb'))
            else:
                return FileResponse(open(project_file.target_bilingualfile.path, 'rb'))

    return render(request, 'project.html', {'files':project_files, 'project':project})

@login_required
def editor(request, id):
    project_file = ProjectFile.objects.get(id=id)

    if project_file.translator == request.user \
        or project_file.reviewer == request.user \
        or project_file.project.created_by == request.user \
        or request.user in project_file.project.managed_by.all():
        None
    else:
        return redirect('/accounts/login?next={0}'.format(request.path))

    if request.method == 'POST':
        if request.POST.get('task') == 'update_segment':
            segment_dict = request.POST

            target = segment_dict['target'] \
                     .replace(' contenteditable="false" draggable="true">', '>') \
                     .replace('&nbsp;', ' ')

            bf = open_bilingualfile(project_file.target_bilingualfile.path)
            bf.update_segment('<target>' + target + '</target>',
                              segment_dict['tu_id'],
                              segment_dict['s_id'],
                              segment_dict['status'])
            bf.save(project_file.get_target_directory())

            segment = Segment.objects.filter(file=project_file) \
                      .filter(tu_id=segment_dict['tu_id']) \
                      .get(s_id=segment_dict['s_id'])
            segment.target = target
            segment.status = ('blank', 'draft','translated').index(segment_dict['status'])
            segment.updated_by = request.user
            segment.save()

            for tm in project_file.project.translationmemories.all():
                try:
                    tm_entry = TMEntry.objects.filter(translationmemory=tm).get(source=segment.source)
                    if tm_entry.target == target:
                        continue
                    tm_entry.target = target
                    tm_entry.updated_by = request.user
                    tm_entry.save()
                except:
                    tm_entry = TMEntry()
                    tm_entry.source = segment.source
                    tm_entry.target = segment.target
                    tm_entry.translationmemory = tm
                    tm_entry.created_by = tm_entry.updated_by = request.user
                    tm_entry.save()

            return JsonResponse(request.POST)

    else:
        bilingualfile = open_bilingualfile(project_file.target_bilingualfile.path)

        if request.GET.get('task') == 'lookup':
            segment_dict = request.GET
            segment_source = Segment.objects.filter(file=project_file) \
                             .filter(tu_id=segment_dict['tu_id']) \
                             .get(s_id=segment_dict['s_id']).source
            tm_entries = []

            for tm in project_file.project.translationmemories.all():
                for relevant_tm_entry in TMEntry.objects.filter(translationmemory=tm):
                    if relevant_tm_entry.source == segment_source and relevant_tm_entry.target != '':
                        tm_entries.append((relevant_tm_entry.id, {'source': relevant_tm_entry.source,
                                                                  'target': relevant_tm_entry.target,
                                                                  'updated_by': relevant_tm_entry.updated_by.username,
                                                                  'updated_at': relevant_tm_entry.updated_at}))

            return JsonResponse(dict(tm_entries))
        else:
            translation_units = {}
            for segment_instance in Segment.objects.filter(file=project_file).order_by('s_id'):
                if segment_instance.tu_id not in translation_units:
                    translation_units[segment_instance.tu_id] = {}
                translation_units[segment_instance.tu_id][segment_instance.s_id] = segment_instance

            return render(request, 'editor.html', {'file':project_file, 'translation_units':translation_units})

@login_required
def translation_memories(request):
    source_language = request.GET.get('source-language')
    target_language = request.GET.get('target-language')

    translation_memories = TranslationMemory.objects.all()
    if source_language:
        translation_memories = translation_memories.filter(source_language=source_language)
    if target_language:
        translation_memories = translation_memories.filter(target_language=target_language)

    if request.GET.get('format') == 'JSON':
        tm_dict = {}
        for tm in translation_memories:
            tm_dict[tm.id] = tm.name
        return JsonResponse(tm_dict)
    else:
        return render(request, 'translation-memories.html', {'at_tms':True, 'tms':translation_memories})

@login_required
def translation_memory(request, id):
    tm_entries = TMEntry.objects \
                .filter(translationmemory=TranslationMemory.objects.get(id=id)) \
                .exclude(target='')

    return render(request, 'tm.html', {'tm_entries':tm_entries})

def login(request):
    from django.contrib.auth import login
    from django.contrib.auth.forms import AuthenticationForm

    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if request.POST.get('next') != '':
                return HttpResponseRedirect(request.POST['next'])
            else:
                return redirect('projects')
        else:
            return render(request, 'accounts/login.html', {'form':form})

    else:
        form = AuthenticationForm()
        return render(request, 'accounts/login.html', {'form':form, 'next':request.GET.get('next', '')})

def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('projects')
