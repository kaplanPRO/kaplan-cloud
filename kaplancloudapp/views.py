from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.shortcuts import redirect, render

from .forms import KPPUploadForm, ProjectForm, SearchForm, AssignLinguistForm, \
                   SegmentCommentForm, TranslationMemoryForm, \
                   TranslationMemoryImportForm
from .models import Client, Comment, ProjectFile, ProjectPackage, \
                    ProjectPreprocessingSettings, ProjectReferenceFile, \
                    ProjectReport, Project, Segment, TranslationMemory, TMEntry

from .thread_classes import CreateTargetBilingualFileThread, \
                            GenerateTargetTranslationThread, \
                            ImportTargetBilingualFile, TMImportThread

from datetime import datetime
import difflib
import json
from pathlib import Path
import tempfile
import zipfile

from lxml import etree
from kaplan.kdb import KDB
from kaplan.project import Project as KPP

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

        if form.cleaned_data['will_pretranslate']:
            proj_pre_settings = ProjectPreprocessingSettings()
            proj_pre_settings.project = new_project
            proj_pre_settings.will_pretranslate = True
            proj_pre_settings.save()

        for tm in form.cleaned_data['translation_memories']:
            new_project.translationmemories.add(tm)

        new_project.directory = str(Path(settings.PROJECTS_DIR,
                                         str(new_project.uuid)))
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
                new_file.bilingual_file.save(new_file_name, file)
            new_file.save()

        for file in form.files.getlist('reference_files'):
            new_ref_file = ProjectReferenceFile()
            new_ref_file.name = file.name
            new_ref_file.project = new_project
            new_ref_file.reference_file.save(file.name, file)
            new_ref_file.save()

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
        tm.created_by = request.user
        tm.client = form.cleaned_data['client']
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

    client_accounts_for_user = Client.objects.filter(team=request.user)

    projects = list(
        projects.filter(created_by=request.user)
        |
        projects.filter(managed_by=request.user)
        |
        projects.filter(client__in=client_accounts_for_user))

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
def project(request, uuid):
    project = Project.objects.get(uuid=uuid)
    project_files = ProjectFile.objects.filter(project=project)
    if (
        not request.user.has_perm('kaplancloudapp.change_projectfile') \
        and project.created_by != request.user \
        and request.user not in project.managed_by.all()
       ) and not (
            project.client is not None 
            and
            request.user in project.client.team.all()
        ):
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
            threads = []
            Path('.tmp').mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(dir='.tmp') as tmpdir:
                for pf_id in request.POST['file_uuids'].split(';'):
                    project_file = project_files.get(uuid=pf_id)
                    threads.append(GenerateTargetTranslationThread(project_file,
                                                                   tmpdir))

                for thread in threads: thread.start()
                for thread in threads: thread.join()

                tmpdir_files = [tmpdir_file for tmpdir_file in list(Path(tmpdir).iterdir()) if not tmpdir_file.is_dir()]

                if len(tmpdir_files) > 1:
                    tmpzip_path = Path(tmpdir) / 'target.zip'
                    with zipfile.ZipFile(tmpzip_path, 'w') as tmpzip:
                        for tmpdir_file in tmpdir_files:
                            tmpzip.write(tmpdir_file, tmpdir_file.name)
                    return FileResponse(open(tmpzip_path, 'rb'))
                else:
                    return FileResponse(open(tmpdir_files[0], 'rb'))
        elif not request.user.has_perm('kaplancloudapp.change_project'):
            return JsonResponse({'message':'forbidden'}, status=403)
        elif request.POST.get('task') == 'analyze':
            projectreport_instance = ProjectReport()
            projectreport_instance.project = project
            projectreport_instance.content = {'status':'processing'}
            projectreport_instance.created_by = request.user
            projectreport_instance.save()

            for file_uuid in request.POST['file_uuids'].split(';'):
                projectreport_instance.project_files.add(project_files.get(uuid=file_uuid))
            projectreport_instance.status = 1
            projectreport_instance.save()

            return JsonResponse({'uuid':projectreport_instance.uuid})

        elif request.POST.get('task') == 'export':
            files_manifest = {}

            files_to_export = [id for id in request.POST['file_uuids'].split(';') if id != '']

            if len(files_to_export) == 0:
                return JsonResponse({'error':'No files selected'}, status=500)

            project_manifest = project.get_manifest()

            threads = []

            Path('.tmp').mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(dir='.tmp') as p_tmpdir:
                project_manifest['directory'] = p_tmpdir

                p_s_tmpdir = Path(p_tmpdir, project.source_language)
                p_s_tmpdir.mkdir()

                p_t_tmpdir = Path(p_tmpdir, project.target_language)
                p_t_tmpdir.mkdir()


                for project_file_instance in ProjectFile.objects.filter(project=project):
                    file_manifest = {}
                    if project_file_instance.source_file:
                        path_source = p_s_tmpdir / Path(project_file_instance.source_file.name).name
                        path_source.write_bytes(project_file_instance.source_file.read())
                        file_manifest['source'] = str(path_source)
                    if project_file_instance.bilingual_file:
                        path_source_bf = p_s_tmpdir / Path(project_file_instance.bilingual_file.name).name
                        path_source_bf.write_bytes(project_file_instance.bilingual_file.read())
                        file_manifest['originalBF'] = str(path_source_bf)

                        path_target_bf = p_t_tmpdir / Path(project_file_instance.bilingual_file.name).name
                        threads.append(CreateTargetBilingualFileThread(project_file_instance,
                                                                       p_t_tmpdir,
                                                                       path_source_bf))

                        file_manifest['targetBF'] = str(path_target_bf)

                    files_manifest[str(project_file_instance.uuid)] = file_manifest

                for thread in threads: thread.start()
                for thread in threads: thread.join()

                project_manifest['files'] = files_manifest

                project_package = KPP(project_manifest)

                project_package_instance = ProjectPackage()
                project_package_instance.project = project

                with tempfile.TemporaryDirectory(dir='.tmp') as package_tmpdir:
                    path_package = Path(package_tmpdir, (datetime.now().isoformat()+'.kpp'))

                    project_package.export(target_path=str(path_package),
                                           files_to_export=files_to_export)

                    project_package_instance.package.save(path_package.name,
                                                          path_package.open('rb'))

                    project_package_instance.created_by = request.user
                    project_package_instance.save()

                    return FileResponse(path_package.open('rb'))

        elif request.POST.get('task') == 'import':
            form = KPPUploadForm(request.POST, request.FILES)

            threads = []

            Path('.tmp').mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(dir='.tmp') as tmpdir:
                with zipfile.ZipFile(form.files.getlist('package')[0]) as kpp:
                    manifest = json.loads(kpp.read('manifest.json'))


                    for i, file in manifest['files'].items():
                        project_file_instance = ProjectFile.objects.filter(project=project) \
                                                .get(bilingual_file__endswith=Path(file['targetBF']).name)

                        path_target_bf = Path(tmpdir, Path(file['targetBF']).name)
                        path_target_bf.write_bytes(kpp.read(file['targetBF']))

                        threads.append(ImportTargetBilingualFile(project_file_instance,
                                                                 path_target_bf))

                for thread in threads: thread.start()
                for thread in threads: thread.join()

        elif request.POST.get('task') == 'assign_linguist':
            form1 = AssignLinguistForm(request.POST)

            if form1.is_valid():
                for f_uuid in request.POST['file_uuids'].split(';'):
                    project_file = project_files.get(uuid=f_uuid)
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
                   'reference':ProjectReferenceFile.objects.filter(project=project),
                   'form':form,
                   'form1':form1,
                   'project':project,
                   'reports':ProjectReport.objects.filter(project=project).filter(status=3)
                  })

@login_required
def editor(request, uuid):
    project_file = ProjectFile.objects.get(uuid=uuid)

    if request.user.has_perm('kaplancloudapp.change_projectfile') \
        or request.user == project_file.project.created_by \
        or request.user in project_file.project.managed_by.all() \
        or (
            project_file.project.client is not None 
            and
            request.user in project_file.project.client.team.all()):
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
            segment = Segment.objects.filter(file=project_file) \
                      .filter(tu_id=segment_dict['tu_id']) \
                      .get(s_id=segment_dict['s_id'])

            if segment.is_locked:
                return JsonResponse({'message':'locked'}, status=403)

            cur_target = segment.target
            cur_updated_by = segment.updated_by

            target = segment_dict['target'] \
                     .replace(' contenteditable="false" draggable="true">', '>') \
                     .replace('&nbsp;', ' ')

            segment.target = target
            segment.status = ('blank', 'draft','translated').index(segment_dict['status'])
            segment.updated_by = request.user
            segment.save(cur_target=cur_target,cur_updated_by=cur_updated_by)

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

        elif request.POST.get('task') == 'change_segment_locks':
            relevant_segments = Segment.objects.filter(file=project_file)
            to_lock = request.POST['to_lock'] == 'lock'
            for s_id in request.POST['segments'].split(';'):
                relevant_segment = relevant_segments.get(s_id=s_id)
                if relevant_segment.is_locked == to_lock:
                    continue
                relevant_segment.is_locked = to_lock
                relevant_segment.save(no_override=True)

            return JsonResponse({'message':'success'})

    else:
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
def reference_file(request, uuid):
    reference_file_instance = ProjectReferenceFile.objects.get(uuid=uuid)

    is_relevant = True
    if not not request.user.has_perm('kaplancloudapp.view_projectreferencefile') \
    and request.user not in reference_file_instance.project.managed_by.all() \
    and request.user != reference_file_instance.project.created_by:
        is_relevant = False
        for project_file_instance in ProjectFile.objects.filter(project=reference_file_instance.project):
            if request.user == project_file_instance.translator \
            or request.user == project_file_instance.reviewer:
                is_relevant = True
                break

    if is_relevant:
        return FileResponse(reference_file_instance.reference_file.open())
    else:
        return redirect('/accounts/login?next={0}'.format(request.path))

@login_required
def report(request, uuid):
    project_report = ProjectReport.objects.get(uuid=uuid)
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

    if not request.user.has_perm('kaplancloudapp.view_translationmemory'):
        translation_memories = translation_memories \
            .filter(client__in=Client.objects.filter(team=request.user))

    if request.GET.get('format') == 'JSON':
        tm_dict = {}
        for tm in translation_memories:
            tm_dict[tm.id] = tm.name
        return JsonResponse(tm_dict)
    else:
        return render(request, 'translation-memories.html', {'at_tms':True, 'tms':translation_memories, 'form':form, 'display_form':display_form})

@login_required
def translation_memory(request, uuid):
    tm = TranslationMemory.objects.get(uuid=uuid)

    if (
        not request.user.has_perm('kaplancloudapp.view_translationmemory')
        and
        not (
            tm.client is not None and request.user not in tm.client.team.all()
        )
    ):
        return redirect('/accounts/login?next={0}'.format(request.path))

    tm_entries = TMEntry.objects \
        .filter(translationmemory=tm) \
        .exclude(target='')

    return render(request, 'tm.html', {'tm_entries':tm_entries, 'tm_uuid':tm.uuid})

@login_required
@permission_required('kaplancloudapp.add_translationmemory')
def translation_memory_import(request, uuid):
    translation_memory = TranslationMemory.objects.get(uuid=uuid)
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

        return redirect('tm', uuid=translation_memory.uuid)

    return render(request, 'tm-import.html', {'form':form})
