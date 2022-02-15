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
