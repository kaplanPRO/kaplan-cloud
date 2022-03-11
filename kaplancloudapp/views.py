from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files import File
from django.core.serializers import serialize
from django.http import FileResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect, render

from .forms import KPPUploadForm, ProjectForm, SearchForm, AssignLinguistForm, \
                   SegmentCommentForm, TranslationMemoryForm, \
                   TranslationMemoryImportForm
from .models import Client, Comment, ProjectFile, ProjectPackage, \
                    ProjectReport, Project, Segment, TranslationMemory, TMEntry

from .thread_classes import TMImportThread

from datetime import datetime
import difflib
import json
from pathlib import Path
import tempfile
import zipfile

from lxml import etree
from kaplan import open_bilingualfile
from kaplan.kdb import KDB
from kaplan.project import Project as KPP

from .utils import trim_segment

# Create your views here.

@login_required
@permission_required('kaplancloudapp.add_project')
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
        if form.cleaned_data.get('client'):
            new_project.client = form.cleaned_data['client']
        new_project.save()

        for tm in form.cleaned_data['translation_memories']:
            new_project.translationmemories.add(tm)

        new_project.directory = str(Path(settings.PROJECTS_DIR,
                                         str(new_project.id)))
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

        new_project._are_all_files_submitted = True
        new_project.save()

        return redirect('projects')

    return render(request, 'newproject.html', {'form':form})

@login_required
@permission_required('kaplancloudapp.add_translationmemory')
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
    form = SearchForm(request.GET)
    display_form = False

    projects = Project.objects.all()

    if request.GET.get('source'):
        projects = projects.filter(source_language=request.GET['source'])
        display_form = True

    if request.GET.get('target'):
        projects = projects.filter(target_language=request.GET['target'])
        display_form = True

    if request.GET.get('client'):
        client = Client.objects.get(id=request.GET['client'])
        projects = projects.filter(client=client)
        display_form = True

    projects = list(projects.filter(created_by=request.user) | projects.filter(managed_by=request.user))

    project_files = ProjectFile.objects.all()
    for project in projects:
        project_files = project_files.exclude(project=project)

    project_files = project_files.filter(translator=request.user) \
                  | project_files.filter(reviewer=request.user)

    project_files = project_files.filter(status__gte=4) \
                  & project_files.filter(status__lte=6)

    for project_file in project_files:
        if project_file.project not in projects:
            projects.append(project_file.project)

    return render(request, 'projects.html', {'at_projects':True, 'projects':projects, 'form':form, 'display_form':display_form})

@login_required
def project(request, id):
    project = Project.objects.get(id=id)
    project_files = ProjectFile.objects.filter(project=project)
    if not request.user.has_perm('kaplancloudapp.change_projectfile') \
       and project.created_by != request.user \
       and request.user not in project.managed_by.all():
        project_files = project_files.filter(translator=request.user) \
                      | project_files.filter(reviewer=request.user)

        project_files = project_files.filter(status__gte=4) \
                      & project_files.filter(status__lte=6)

        if len(project_files) == 0:
            return redirect('/accounts/login?next={0}'.format(request.path))

    form = KPPUploadForm()
    form1 = AssignLinguistForm()

    if request.method == 'POST':
        if request.POST.get('task') == 'download_translations':
            with tempfile.TemporaryDirectory() as tempdir:
                for pf_id in request.POST['file_ids'].split(';'):
                    project_file = project_files.get(id=int(pf_id))
                    if project_file.source_file is not None:
                        bf = open_bilingualfile(project_file.target_bilingualfile.path)
                        bf.generate_target_translation(tempdir, target_filename=project_file.name)
                    else:
                        with (Path(tempdir) / Path(project_file.target_bilingualfile.path).name).open() as tmpfile:
                            with Path(project_file.target_bilingualfile.path).open() as target_bf:
                                tmpfile.write_bytes(target_bf.read_bytes)

                tempdir_files = [tempdir_file for tempdir_file in list(Path(tempdir).iterdir()) if not tempdir_file.is_dir()]
                if len(tempdir_files) > 1:
                    tmpzip_path = Path(tempdir) / 'target.zip'
                    with zipfile.ZipFile(tmpzip_path, 'w') as tmpzip:
                        for tempdir_file in tempdir_files:
                            tmpzip.write(tempdir_file, tempdir_file.name)
                    return FileResponse(open(tmpzip_path, 'rb'))
                else:
                    return FileResponse(open(tempdir_files[0], 'rb'))
        elif not request.user.has_perm('kaplancloudapp.change_project'):
            return JsonResponse({'message':'forbidden'}, status=403)
        elif request.POST.get('task') == 'analyze':
            projectreport_instance = ProjectReport()
            projectreport_instance.project = project
            projectreport_instance.content = {'status':'processing'}
            projectreport_instance.created_by = request.user
            projectreport_instance.save()

            for file_id in request.POST['file_ids'].split(';')[:-1]:
                projectreport_instance.project_files.add(project_files.get(id=file_id))
            projectreport_instance.status = 1
            projectreport_instance.save()

            return JsonResponse({'id':projectreport_instance.id})

        elif request.POST.get('task') == 'export':
            files_manifest = {}

            project_manifest = project.get_manifest()
            project_directory = Path(project_manifest['directory'])

            for project_file_instance in ProjectFile.objects.filter(project=project):
                file_manifest = {}
                if project_file_instance.source_file is not None:
                    file_manifest['source'] = project_file_instance.source_file.path
                if project_file_instance.source_bilingualfile is not None:
                    file_manifest['originalBF'] = project_file_instance.source_bilingualfile.path

                file_manifest['targetBF'] = project_file_instance.target_bilingualfile.path

                files_manifest[project_file_instance.id] = file_manifest

            project_manifest['files'] = files_manifest

            project_package = KPP(project_manifest)

            project_package_instance = ProjectPackage()
            project_package_instance.project = project

            path_to_package = Path(project_package.directory) / 'packages' / (datetime.now().isoformat()+'.kpp')
            path_to_package.parent.mkdir(parents=True, exist_ok=True)

            project_package.export(target_path=str(path_to_package),
                                   files_to_export=[int(i) for i in request.POST['file_ids'].split(';')[:-1]])

            project_package_instance.package.name = str(path_to_package)
            project_package_instance.created_by = request.user
            project_package_instance.save()

            return FileResponse(open(path_to_package, 'rb'))

        elif request.POST.get('task') == 'import':
            form = KPPUploadForm(request.POST, request.FILES)

            with zipfile.ZipFile(form.files.getlist('package')[0]) as kpp:
                manifest = json.loads(kpp.read('manifest.json'))

                for i, file in manifest['files'].items():
                    project_file_instance = ProjectFile.objects.filter(project=project) \
                                            .get(target_bilingualfile__endswith=file['targetBF'])

                    project_file_segments = Segment.objects.filter(file=project_file_instance)

                    tmp_path = Path('kaplancloudapp/.tmp/') / Path(file['targetBF']).name

                    while tmp_path.exists():
                        tmp_path = tmp_path.parent / (tmp_path.stem + '_' + tmp_path.suffix)

                    with open(tmp_path, 'wb') as targetbf:
                        targetbf.write(kpp.read(file['targetBF']))

                    for package_tu in open_bilingualfile(str(tmp_path)).gen_translation_units():
                        if package_tu.attrib.get('id') is None:
                            continue
                        relevant_segments = project_file_segments.filter(tu_id=package_tu.attrib['id'])
                        for package_segment in package_tu:
                            if package_segment.attrib.get('id') is None:
                                continue

                            package_target = trim_segment(package_segment[1])

                            relevant_segment = relevant_segments.get(s_id=package_segment.attrib['id'])
                            relevant_segment.target = package_target
                            relevant_segment.updated_by = request.user
                            relevant_segment.save()

                    tmp_path.unlink()

        elif request.POST.get('task') == 'assign_linguist':
            form1 = AssignLinguistForm(request.POST)

            if form1.is_valid():
                for f_id in request.POST['file_ids'].split(';'):
                    project_file = project_files.get(id=f_id)
                    if int(request.POST['role']) == 0:
                        if project_file.translator is not None and request.POST.get('override') is None:
                            continue
                        project_file.translator = User.objects.get(username=request.POST['username'])
                        project_file.save()
                    elif int(request.POST['role']) == 1:
                        if project_file.reviewer is not None and request.POST.get('override') is None:
                            continue
                        project_file.reviewer = User.objects.get(username=request.POST['username'])
                        project_file.save()

    return render(request,
                  'project.html',
                  {'files':project_files,
                   'form':form,
                   'form1':form1,
                   'project':project,
                   'reports':ProjectReport.objects.filter(project=project).filter(status=3)
                  })

@login_required
def editor(request, id):
    project_file = ProjectFile.objects.get(id=id)

    if request.user.has_perm('kaplancloudapp.change_projectfile') \
        or request.user == project_file.project.created_by \
        or request.user in project_file.project.managed_by.all():
        can_edit = project_file.status < 7
    elif ((project_file.translator == request.user \
        or project_file.reviewer == request.user) \
        and project_file.status >= 4 and project_file.status <= 6):
        if project_file.translator == request.user and project_file.status == 4:
            can_edit = True
        elif project_file.reviewer == request.user and project_file.status == 5:
            can_edit = True
        else:
            can_edit = False
    else:
        return redirect('/accounts/login?next={0}'.format(request.path))

    form = SegmentCommentForm(request.POST or None)

    if request.method == 'POST':
        if request.POST.get('task') == 'update_segment':
            if not can_edit:
                return JsonResponse({'message':'forbidden'}, status=403)
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

            if segment.status < 2:
                return JsonResponse(request.POST)

            # Convert segment to segment entry format for better TM matches
            source = etree.fromstring('<source>' + segment.source + '</source>')
            source, _ = KDB.segment_to_entry(source)

            target = etree.fromstring('<target>' + target + '</target>')
            target, _ = KDB.segment_to_entry(target)

            for tm in project_file.project.translationmemories.all():
                try:
                    tm_entry = TMEntry.objects.filter(translationmemory=tm).get(source=source)
                    if tm_entry.target == target:
                        continue
                    tm_entry.target = target
                    tm_entry.updated_by = request.user
                    tm_entry.save()
                except TMEntry.DoesNotExist:
                    tm_entry = TMEntry()
                    tm_entry.source = source
                    tm_entry.target = target
                    tm_entry.translationmemory = tm
                    tm_entry.created_by = tm_entry.updated_by = request.user
                    tm_entry.save()

            return JsonResponse(request.POST)

        elif request.POST.get('task') == 'add_comment':
            comment = request.POST['comment']
            segment_id = request.POST['segment_id']

            relevant_segment = Segment.objects.filter(file=project_file) \
                                              .get(s_id=segment_id)

            comment_instance = Comment()
            comment_instance.comment = comment
            comment_instance.segment = relevant_segment
            comment_instance.created_by = request.user
            comment_instance.save()

            comment_dict = {
                'comment': comment_instance.comment,
                'created_by': comment_instance.created_by.username,
                'created_at': comment_instance.created_at
            }

            return JsonResponse(comment_dict)

        elif request.POST.get('task') == 'advance_file_status':
            if not can_edit:
                return JsonResponse({'message':'forbidden'}, status=403)

            project_file.status += 1
            project_file.save()

            return JsonResponse({'message':'success'})

    else:
        bilingualfile = open_bilingualfile(project_file.target_bilingualfile.path)

        if request.GET.get('task') == 'lookup':
            segment_dict = request.GET
            segment = Segment.objects.filter(file=project_file) \
                      .filter(tu_id=segment_dict['tu_id']) \
                      .get(s_id=segment_dict['s_id'])
            segment_source = '<source>' + segment.source + '</source>'
            segment_source = etree.fromstring(segment_source)


            source_entry, tags = KDB.segment_to_entry(segment_source, {})
            reversed_tags = {v: k for k, v in tags.items()}

            sm = difflib.SequenceMatcher()
            sm.set_seq2(source_entry)

            tm_entries = []
            for tm in project_file.project.translationmemories.all():
                for relevant_tm_entry in TMEntry.objects.filter(translationmemory=tm):
                    tm_entry_source = KDB.entry_to_segment(relevant_tm_entry.source, 'source', reversed_tags, segment_source)
                    tm_entry_source = etree.tostring(tm_entry_source, encoding='UTF-8').decode()[8:-9]

                    tm_entry_target = KDB.entry_to_segment(relevant_tm_entry.target, 'target', reversed_tags, segment_source)
                    tm_entry_target = etree.tostring(tm_entry_target, encoding='UTF-8').decode()[8:-9]
                    if relevant_tm_entry.source == source_entry and relevant_tm_entry.target != '':
                        tm_entries.append((1.0, {'source': tm_entry_source,
                                                 'target': tm_entry_target,
                                                 'updated_by': relevant_tm_entry.updated_by.username,
                                                 'updated_at': relevant_tm_entry.updated_at}))
                        continue

                    sm.set_seq1(tm_entry_source)
                    diff = sm.ratio()
                    if diff >= 0.5:
                        tm_entries.append((diff, {'source': tm_entry_source,
                                                  'target': tm_entry_target,
                                                  'updated_by': relevant_tm_entry.updated_by.username,
                                                  'updated_at': relevant_tm_entry.updated_at}))

            tm_entries.sort(reverse=True)

            comments = []
            for comment in Comment.objects.filter(segment=segment):
                comments.append((comment.id, {'comment':comment.comment,
                                              'created_by':comment.created_by.username if comment.created_by else 'N/A',
                                              'created_at':comment.created_at}))

            return JsonResponse({'tm':tm_entries, 'comments':dict(comments)})
        elif request.GET.get('task') == 'concordance':
            query = request.GET['query']

            tm_entries = []
            for tm in project_file.project.translationmemories.all():
                relevant_tm_entries = TMEntry.objects.filter(translationmemory=tm)
                relevant_tm_entries = relevant_tm_entries.filter(source__contains=query) \
                                    | relevant_tm_entries.filter(target__contains=query)

                for relevant_tm_entry in relevant_tm_entries:
                    tm_entry_source = KDB.entry_to_segment(relevant_tm_entry.source, 'source')
                    tm_entry_source = etree.tostring(tm_entry_source, encoding='UTF-8').decode()[8:-9]

                    tm_entry_target = KDB.entry_to_segment(relevant_tm_entry.target, 'target')
                    tm_entry_target = etree.tostring(tm_entry_target, encoding='UTF-8').decode()[8:-9]

                    if query in tm_entry_source and query not in tm_entry_target:
                        len_diff = abs(len(query) - len(tm_entry_source))
                    elif query not in tm_entry_source and query in tm_entry_target:
                        len_diff =  abs(len(query) - len(tm_entry_target))
                    else:
                        len_diff = abs(len(query) - ((len(tm_entry_source) + len(tm_entry_target))/2))

                    tm_entries.append((len_diff,
                                       {'source': tm_entry_source,
                                        'target': tm_entry_target,
                                        'updated_by': relevant_tm_entry.updated_by.username,
                                        'updated_at': relevant_tm_entry.updated_at
                                       }))

                    tm_entries.sort()

            return JsonResponse({'concordance': tm_entries})

        else:
            translation_units = {}
            for segment_instance in Segment.objects.filter(file=project_file).order_by('s_id'):
                if segment_instance.tu_id not in translation_units:
                    translation_units[segment_instance.tu_id] = {}
                translation_units[segment_instance.tu_id][segment_instance.s_id] = segment_instance

            return render(request, 'editor.html', {'file':project_file, 'translation_units':translation_units, 'form':form, 'can_edit':can_edit})

@login_required
def report(request, id):
    project_report = ProjectReport.objects.get(id=id)
    if request.GET.get('task') == 'get_status':
        return JsonResponse({'status':project_report.status})
    project_report = project_report.content
    total_report = project_report['Total']
    del(project_report['Total'])
    return render(request, 'report.html', {'total':total_report, 'files':project_report})

@login_required
def translation_memories(request):
    form = SearchForm(request.GET)
    display_form = False

    translation_memories = TranslationMemory.objects.all()

    if request.GET.get('source'):
        translation_memories = translation_memories.filter(source_language=request.GET['source'])
        display_form = True

    if request.GET.get('target'):
        translation_memories = translation_memories.filter(target_language=request.GET['target'])
        display_form = True

    if request.GET.get('client'):
        client = Client.objects.get(id=request.GET['client'])
        translation_memories = translation_memories.filter(client=client)
        display_form = True

    if request.GET.get('format') == 'JSON':
        tm_dict = {}
        for tm in translation_memories:
            tm_dict[tm.id] = tm.name
        return JsonResponse(tm_dict)
    else:
        return render(request, 'translation-memories.html', {'at_tms':True, 'tms':translation_memories, 'form':form, 'display_form':display_form})

@login_required
def translation_memory(request, id):
    tm_entries = TMEntry.objects \
                .filter(translationmemory=TranslationMemory.objects.get(id=id)) \
                .exclude(target='')

    return render(request, 'tm.html', {'tm_entries':tm_entries, 'tm_id':id})

@login_required
@permission_required('kaplancloudapp.add_translationmemory')
def translation_memory_import(request, id):
    translation_memory = TranslationMemory.objects.get(id=id)
    form = TranslationMemoryImportForm(request.POST or None,
                                       request.FILES or None,
                                       initial={'source_language':translation_memory.source_language,
                                                'target_language':translation_memory.target_language}
                                       )

    if form.is_valid():
        tm_file = form.cleaned_data['tm_file']

        tmp_path = Path('kaplancloudapp/.tmp/') / tm_file.name

        while tmp_path.exists():
            tmp_path = tmp_path.parent / (tmp_path.stem + '_' + tmp_path.suffix)

        with open(tmp_path, 'wb') as target:
            target.write(tm_file.read())

        entries = []

        if tmp_path.suffix.lower() == '.kdb':
            kdb = KDB(str(tmp_path),
                      form.cleaned_data['source_language'],
                      form.cleaned_data['target_language'])

            entries = kdb.get_entries()

            tmp_path.unlink()
        elif tmp_path.suffix.lower() == '.tmx':
            tmp_path2 = tmp_path.parent / (tmp_path.stem + '.kdb')

            while tmp_path2.exists():
                tmp_path2 = tmp_path2.parent / (tmp_path2.steam + '_' + '.kdb')

            kdb = KDB.new(str(tmp_path2),
                          form.cleaned_data['source_language'],
                          form.cleaned_data['target_language'])

            kdb.import_tmx(tmp_path)

            entries = kdb.get_entries()

            tmp_path.unlink()
            tmp_path2.unlink()

        relevant_tm_entries = TMEntry.objects.filter(translationmemory=translation_memory)

        sliced_entries = []
        while len(entries) > 500:
            sliced_entries.append(entries[:500])
            entries = entries[500:]

        if len(entries) > 0:
            sliced_entries.append(entries)

        threads = []

        for entries in sliced_entries:
            new_thread = TMImportThread(entries,
                                        TMEntry,
                                        translation_memory,
                                        relevant_tm_entries)
            threads.append(new_thread)

        for thread in threads:
            thread.start()

        while max([thread.is_alive() for thread in threads]):
            None

        return redirect('tm', id=translation_memory.id)

    return render(request, 'tm-import.html', {'form':form})
