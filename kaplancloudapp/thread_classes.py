from django.apps import apps
from lxml import etree
from kaplan import open_bilingualfile
from kaplan.kdb import KDB
from kaplan.kxliff import KXLIFF

import difflib
from pathlib import Path
import regex
import string
import tempfile
import threading


class GenerateTargetTranslationThread(threading.Thread):
    def __init__(self, file_instance, target_dir, **kwargs):
        super().__init__(**kwargs)
        self.file_instance = file_instance
        self.target_dir = target_dir

    def run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_bf_path = Path(tmpdir, Path(self.file_instance.target_bilingualfile.url).name)
            target_bf_path.write_bytes(self.file_instance.target_bilingualfile.read())

            bf = open_bilingualfile(target_bf_path)

        relevant_segments = apps.get_model('kaplancloudapp', 'Segment') \
                            .objects.filter(file=self.file_instance)

        for relevant_segment in relevant_segments:
            bf.update_segment('<target>' + relevant_segment.target + '</target>',
            relevant_segment.tu_id,
            relevant_segment.s_id,
            segment_state=('blank', 'draft','translated')[int(relevant_segment.status)])

        if self.file_instance.source_file:

            with tempfile.TemporaryDirectory() as tmpdir:
                path_source = Path(tmpdir, Path(self.file_instance.source_file.url).name)
                path_source.write_bytes(self.file_instance.source_file.read())

                bf.generate_target_translation(self.target_dir,
                                               path_to_source_file=path_source,
                                               target_filename=self.file_instance.name)
        else:
            bf.save(self.target_dir)


class NewFileThread(threading.Thread):
    def __init__(self, file_instance, **kwargs):
        self.file_instance = file_instance
        super(NewFileThread, self).__init__(**kwargs)

    def run(self):
        instance = self.file_instance

        try:
            project_directory = Path(instance.project.directory)

            if instance.source_file \
            and not instance.source_bilingualfile \
            and not instance.target_bilingualfile:

                bilingualfile = KXLIFF.new(instance.source_file.path,
                                           instance.source_language,
                                           instance.target_language)

                with tempfile.TemporaryDirectory() as tempdir:
                    bilingualfile.save(tempdir)
                    with open(Path(tempdir, bilingualfile.name)) as bf:
                        instance.source_bilingualfile.save(bilingualfile.name,
                                                           bf)
                        instance.target_bilingualfile.save(bilingualfile.name,
                                                           bf)

                instance.save()

            elif (instance.source_bilingualfile
            and not instance.target_bilingualfile):

                bilingualfile = open_bilingualfile(instance.source_bilingualfile.path)

                with tempfile.TemporaryDirectory() as tempdir:
                    bilingualfile.save(tempdir)

                    with open(Path(tempdir, bilingualfile.name)) as bf:
                        instance.target_bilingualfile.save(bilingualfile.name,
                                                           bf)

                instance.save()

            bilingualfile = open_bilingualfile(instance.target_bilingualfile.path)

            SegmentModel = apps.get_model('kaplancloudapp', 'Segment')

            _regex_source = regex.compile('<source[^<>]*?>(.*)</source>')
            _regex_target = regex.compile('<target[^<>]*?>(.*)</target>')
            for xml_translation_unit in bilingualfile.gen_translation_units():
                for xml_segment in xml_translation_unit:
                    if xml_segment.tag.split('}')[-1] == 'ignorable':
                        continue

                    segment = SegmentModel()
                    segment.tu_id = xml_translation_unit.attrib['id']
                    segment.s_id = xml_segment.attrib.get('id', 'N/A')

                    segment_source = etree.tostring(xml_segment.find('source', xml_segment.nsmap), encoding='UTF-8').decode()
                    segment_source = _regex_source.match(segment_source)
                    if segment_source is not None:
                        segment.source = segment_source.group(1)
                    else:
                        segment.source = ''

                    segment_target = xml_segment.find('target', xml_segment.nsmap)
                    if segment_target.text is None and len(segment_target) == 0:
                        segment.target = ''
                    else:
                        segment_target = etree.tostring(segment_target, encoding='UTF-8').decode()
                        segment_target = _regex_target.match(segment_target)
                        if segment_target is not None:
                            segment.target = segment_target.group(1)
                        else:
                            segment.target = ''

                    segment.file = instance
                    segment.created_by = instance.project.created_by
                    segment.save()

            instance.status = 1
            instance.save()
        except ValueError as error:
            instance.status = -1
            instance.save()


class NewProjectReportThread(threading.Thread):
    def __init__(self, projectreport_instance, **kwargs):
        self.projectreport_instance = projectreport_instance
        super(NewProjectReportThread, self).__init__(**kwargs)

    def run(self):
        instance = self.projectreport_instance

        for project_file in instance.project_files.all():
            if project_file.status == 1:
                project_file.status = 2
                project_file.save()

        SegmentModel = apps.get_model('kaplancloudapp', 'Segment')

        entries = []

        project_report = {}
        project_total = {'Repetitions': 0,
                         '100': 0, # TODO
                         '95': 0,
                         '85': 0,
                         '75': 0,
                         '50': 0,
                         'New': 0,
                         'Total': 0
                        }

        sm = difflib.SequenceMatcher()
        for project_file in instance.project_files.all():
            file_report = {'Repetitions': 0,
                           '100': 0, # TODO
                           '95': 0,
                           '85': 0,
                           '75': 0,
                           '50': 0,
                           'New': 0,
                           'Total': 0
                          }

            for segment in SegmentModel.objects.filter(file=project_file):
                source_segment = etree.fromstring('<source>' + segment.source + '</source>')
                source_entry, _ = KDB.segment_to_entry(source_segment)
                word_count = len(source_entry.split())
                char_count = len(source_entry)

                if source_entry in entries:
                    file_report['Repetitions'] += word_count
                # elif entry in project_tm_entries TODO
                else:
                    sm.set_seq2(source_entry)

                    highest_match = 0.0
                    for entry in filter(lambda x: len(x) >= char_count/2 and len(x) <= char_count*2, entries):
                        sm.set_seq1(entry)
                        highest_match = max(sm.ratio(), highest_match)
                        if highest_match >= 0.95:
                            break

                    if highest_match >= 0.95:
                        file_report['95'] += word_count
                    elif highest_match >= 0.85:
                        file_report['85'] += word_count
                    elif highest_match >= 0.75:
                        file_report['75'] += word_count
                    elif highest_match >= 0.5:
                        file_report['50'] += word_count
                    else:
                        file_report['New'] += word_count

                    entries.append(source_entry)

                file_report['Total'] += word_count

            project_total['Repetitions'] += file_report['Repetitions']
            project_total['100'] += file_report['100']
            project_total['95'] += file_report['95']
            project_total['85'] += file_report['85']
            project_total['75'] += file_report['75']
            project_total['50'] += file_report['50']
            project_total['New'] += file_report['New']
            project_total['Total'] += file_report['Total']

            project_report[project_file.name] = file_report

        project_report['Total'] = project_total

        instance.content = project_report
        instance.status = 3
        instance.save()

        for project_file in instance.project_files.all():
            if project_file.status == 2:
                project_file.status = 3
                project_file.save()


class TMImportThread(threading.Thread):
    def __init__(self, entries, TMEntryModel, translation_memory, relevant_tm_entries, **kwargs):
        self.entries = entries
        self.relevant_tm_entries = relevant_tm_entries
        self.TMEntryModel = TMEntryModel
        self.translation_memory = translation_memory
        super(TMImportThread, self).__init__(**kwargs)

    def run(self):
        for entry in self.entries:
            tm_entries = self.relevant_tm_entries.filter(source = entry[1])
            if len(tm_entries) == 1:
                tm_entry = tm_entries[0]
            else:
                tm_entry = self.TMEntryModel()
                tm_entry.source = entry[1]
                tm_entry.translationmemory = self.translation_memory

            tm_entry.target = entry[2]
            tm_entry.save()
