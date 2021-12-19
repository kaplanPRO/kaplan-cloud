from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ProjectFile, ProjectReport, Segment, SegmentUpdate, \
                    TMEntry, TMEntryUpdate

from lxml import etree
from kaplan import open_bilingualfile
from kaplan.kdb import KDB
from kaplan.kxliff import KXLIFF

import difflib
from pathlib import Path
import random
import regex
import string
import threading

@receiver(post_save, sender=ProjectFile)
def new_file_handler(sender, instance, created, **kwargs):
    if not created:
        return

    #class NewFileThread(threading.Thread):
    #    def __init__(self, file_instance, **kwargs):
    #        self.file_instance = file_instance
    #        super(NewFileThread, self).__init__(**kwargs)

    #    def run(self):
    #        instance = self.file_instance
    project_directory = Path(instance.project.directory)

    if (instance.source_file
    and not instance.source_bilingualfile
    and not instance.target_bilingualfile):

        source_directory = project_directory / instance.source_language
        target_directory = project_directory / instance.target_language
        if not source_directory.is_dir():
            source_directory.mkdir()
        if not target_directory.is_dir():
            target_directory.mkdir()

        bilingualfile = KXLIFF.new(instance.source_file.path,
                                   instance.source_language,
                                   instance.target_language)


        source_name = Path(instance.source_file.name).name
        bf_name =  source_name + '.kxliff'
        while (source_directory / bf_name).exists() or (target_directory / bf_name).exists():
            bf_name = ''.join(random.choices(string.ascii_uppercase, k=5)) \
                     + source_name \
                     + '.kxliff'

        bilingualfile.name = bf_name
        bilingualfile.save(str(source_directory))
        instance.source_bilingualfile.name = str(source_directory / bilingualfile.name)
        bilingualfile.save(str(target_directory))
        instance.target_bilingualfile.name = str(target_directory / bilingualfile.name)
        instance.save()

    elif (instance.source_bilingualfile
    and not instance.target_bilingualfile):
        target_directory = project_directory / instance.target_language
        if not target_directory.is_dir():
            target_directory.mkdir()

        bilingualfile = open_bilingualfile(instance.source_bilingualfile.path)
        bilingualfile.save(str(target_directory))
        instance.target_bilingualfile.name = str(target_directory / bilingualfile.name)
        instance.save()

    else:
        bilingualfile = open_bilingualfile(instance.target_bilingualfile.path)

    _regex_source = regex.compile('<source[^<>]*?>(.*)</source>')
    _regex_target = regex.compile('<target[^<>]*?>(.*)</target>')
    for xml_translation_unit in bilingualfile.gen_translation_units():
        for xml_segment in xml_translation_unit:
            if xml_segment.tag.split('}')[-1] == 'ignorable':
                continue

            segment = Segment()
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



    #NewFileThread(instance).start()

@receiver(post_save, sender=ProjectReport)
def new_projectreport_handler(sender, instance, **kwargs):
    if instance.status != 1:
        return

    instance.status = 2
    instance.save()


    class NewProjectReportThread(threading.Thread):
        def __init__(self, projectreport_instance, **kwargs):
            self.projectreport_instance = projectreport_instance
            super(NewProjectReportThread, self).__init__(**kwargs)

        def run(self):
            instance = self.projectreport_instance


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

                for segment in Segment.objects.filter(file=project_file):
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

    NewProjectReportThread(instance).start()


@receiver(post_save, sender=Segment)
def segment_update_handler(sender, instance, created, **kwargs):

    segment_update = SegmentUpdate()
    segment_update.source = instance.source
    segment_update.target = instance.target
    segment_update.status = instance.status
    segment_update.segment = instance
    if created:
        segment_update.submitted_by = instance.created_by
    else:
        segment_update.submitted_by = instance.updated_by
    segment_update.save()

    target_segment = '<target>' + instance.target + '</target>'
    bf = open_bilingualfile(instance.file.target_bilingualfile.path)
    bf.update_segment(target_segment,
                      instance.tu_id,
                      instance.s_id,
                      segment_state=('blank', 'draft','translated')[int(instance.status)])
    bf.save(instance.file.get_target_directory())

@receiver(post_save, sender=TMEntry)
def tmentry_update_handler(sender, instance, created, **kwards):
    tmentry_update = TMEntryUpdate()
    tmentry_update.source = instance.source
    tmentry_update.target = instance.target
    tmentry_update.tmentry = instance
    if created:
        tmentry_update.submitted_by = instance.created_by
    else:
        tmentry_update.submitted_by = instance.updated_by
    tmentry_update.save()
