from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ProjectFile, Segment, SegmentUpdate, TMEntry, TMEntryUpdate

from lxml import etree
from kaplan import open_bilingualfile
from kaplan.kxliff import KXLIFF

from pathlib import Path
import random
import regex
import string
#import threading

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
