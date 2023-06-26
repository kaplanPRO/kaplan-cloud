from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from kaplan import open_bilingualfile

from pathlib import Path
import logging
import shutil
import tempfile
import uuid

from .custom_storage import get_private_storage
from .thread_classes import NewFileThread, NewProjectReportThread
from .utils import get_kpp_path, get_source_file_path, \
                   get_reference_file_path, get_target_file_path

# Create your models here.

file_statuses = project_statuses = (
    (-1, 'Error'),
    (0, 'Preparing'),
    (1, 'Ready for Analysis'),
    (2, 'Analyzing'),
    (3, 'Ready for Translation'),
    (4, 'In Translation'),
    (5, 'In Review'),
    (6, 'Complete'),
    (7, 'Delivered')
)

report_statuses = (
    (0, 'Blank'),
    (1, 'Ready for Processing'),
    (2, 'Processing'),
    (3, 'Complete')
)

segment_statuses = (
    (0, 'Blank'),
    (1, 'Draft'),
    (2, 'Translated')
)


class LanguageProfile(models.Model):
    name = models.CharField(max_length=64)
    iso_code = models.CharField(max_length=10, unique=True)
    is_ltr = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Client(models.Model):
    name = models.CharField(max_length=64)
    team = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return str(self.id) + '-' + self.name


class Termbase(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=64)
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class TBEntry(models.Model):
    source = models.TextField()
    target = models.TextField()
    termbase = models.ForeignKey(Termbase, models.CASCADE)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='tbentry_create')
    updated_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='tbentry_update')
    updated_at = models.DateTimeField(auto_now=True)


class TBEntryUpdate(models.Model):
    source = models.TextField(blank=True)
    target = models.TextField(blank=True)
    tbentry = models.ForeignKey(TBEntry, models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)


class TranslationMemory(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=64)
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    client = models.ForeignKey(Client, models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Translation memories'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tm', kwargs={'uuid' : self.uuid})


class TMEntry(models.Model):
    source = models.TextField()
    target = models.TextField()
    translationmemory = models.ForeignKey(TranslationMemory, models.CASCADE)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='tmentry_create')
    updated_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='tmentry_update')
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.target != '':
            tmentry_update = apps.get_model('kaplancloudapp', 'TMEntryUpdate')()
            tmentry_update.source = self.source
            tmentry_update.target = self.target
            tmentry_update.tmentry = self
            if self.updated_by:
                tmentry_update.submitted_by = self.updated_by
            elif self.created_by:
                tmentry_update.submitted_by = self.created_by
            tmentry_update.save()


class TMEntryUpdate(models.Model):
    source = models.TextField(blank=True)
    target = models.TextField(blank=True)
    tmentry = models.ForeignKey(TMEntry, models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)


class Project(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=64)
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='project_create')
    managed_by = models.ManyToManyField(User, related_name='pm', blank=True)
    termbases = models.ManyToManyField(Termbase, blank=True)
    translationmemories = models.ManyToManyField(TranslationMemory, blank=True)
    status = models.IntegerField(choices=project_statuses, default=0)
    client = models.ForeignKey(Client, models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    directory = models.CharField(max_length=100)
    due_by = models.DateTimeField(blank=True, null=True)
    _are_all_files_submitted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return str(self.id) + '-' + self.name

    def delete(self, *args, **kwargs):
        try:
            if settings.STORAGES['default']['BACKEND'] == 'django.core.files.storage.FileSystemStorage':
                shutil.rmtree(self.directory)
            elif settings.STORAGES['default']['BACKEND'] == 'storages.backends.s3boto3.S3Boto3Storage':
                import boto3

                session = boto3.Session(aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
                                        aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
                                        region_name=settings.AWS_S3_REGION_NAME)

                s3 = session.resource('s3',
                                    endpoint_url=settings.AWS_S3_ENDPOINT_URL)

                bucket = s3.Bucket(settings.S3_PRIVATE_BUCKET_NAME)

                bucket.objects.filter(Prefix=str(Path(settings.S3_PRIVATE_BUCKET_LOCATION, self.directory))).delete()

            elif settings.STORAGES['default']['BACKEND'] == 'storages.backends.gcloud.GoogleCloudStorage':
                from google.cloud import storage

                client = storage.Client()

                bucket = storage.Bucket(client, settings.GS_PRIVATE_BUCKET_NAME)

                blobs = client.list_blobs(bucket,
                                        prefix=str(Path(settings.GS_PRIVATE_BUCKET_LOCATION, self.directory))
                                        )

                bucket.delete_blobs(list(blobs), client=client)

            super().delete(*args, **kwargs)
        except Exception as e:
            logging.error(e)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('project', kwargs={'uuid' : self.uuid})

    def get_manifest(self):
        manifest_dict = {'title':self.name,
                         'directory': str(Path(self.directory).resolve()),
                         'source_language':self.source_language,
                         'target_language':self.target_language,
                        }

        return manifest_dict

    def get_status(self):
        status_dict = dict(project_statuses)
        return status_dict[self.status]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.status == 0 and self.directory.strip() == '':
            project_directory = Path(settings.PROJECTS_DIR, str(self.uuid))
            self.directory = str(project_directory)

            self.save()

        if self.status == 1 and self._are_all_files_submitted:
            ProjectFileModel = apps.get_model('kaplancloudapp', 'ProjectFile')
            project_files = ProjectFileModel.objects.filter(project=self)
            if min([self.status == pf.status for pf in project_files]):
                ProjectReportModel = apps.get_model('kaplancloudapp',
                                                    'ProjectReport')

                new_report = ProjectReportModel()
                new_report.content = {'waitingForFileAssignment':'True'}
                #new_report.created_by = self.created_by
                new_report.project = self
                new_report.save()

                for project_file in project_files:
                    new_report.project_files.add(project_file)

                new_report.status = 1
                new_report.save()


class ProjectFile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.TextField()
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    project = models.ForeignKey(Project, models.CASCADE)
    source_file = models.FileField(storage=get_private_storage, upload_to=get_source_file_path, blank=True, null=True, max_length=256)
    bilingual_file = models.FileField(storage=get_private_storage, upload_to=get_source_file_path, blank=True, null=True, max_length=256)
    status = models.IntegerField(choices=project_statuses, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    due_by = models.DateTimeField(blank=True, null=True)
    translator = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='translator')
    reviewer = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='reviewer')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return '-'.join((str(self.project.id), str(self.id), self.name))

    def delete(self, *args, **kwargs):
        if self.source_file:
            self.source_file.delete(save=False)
        if self.bilingual_file:
            self.bilingual_file.delete(save=False)
        super().delete()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('editor', kwargs={'uuid' : self.uuid})

    def get_source_directory(self):
        return Path(self.project.directory,
                    self.source_language)

    def get_status(self):
        status_dict = dict(file_statuses)
        return status_dict[self.status]

    def get_target_directory(self):
        return Path(self.project.directory,
                    self.target_language)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            NewFileThread(self).run()
            return
        elif self.status == 3 and self.translator is not None:
            self.status = 4
            self.save()
        elif self.project:
            earliest_status_in_project = min([project_file.status for project_file in self.__class__.objects.filter(project=self.project)])
            if self.project.status != earliest_status_in_project:
                self.project.status = earliest_status_in_project
                self.project.save()


class ProjectPackage(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey(Project, models.CASCADE)
    package = models.FileField(storage=get_private_storage, upload_to=get_kpp_path, max_length=256)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def delete(self, *args, **kwargs):
        self.package.delete(save=False)
        super().delete()


class ProjectPreprocessingSettings(models.Model):
    project = models.ForeignKey(Project, models.CASCADE)
    will_pretranslate = models.BooleanField(default=True)


class ProjectReferenceFile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.TextField()
    project = models.ForeignKey(Project, models.CASCADE)
    reference_file = models.FileField(storage=get_private_storage, upload_to=get_reference_file_path, max_length=256)

    def delete(self, *args, **kwargs):
        self.reference_file.delete(save=False)
        super().delete()


class ProjectReport(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey(Project, models.CASCADE)
    project_files = models.ManyToManyField(ProjectFile)
    content = models.JSONField()
    status = models.IntegerField(choices=report_statuses, default=0)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
       ordering = ['-id']

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('report', kwargs={'uuid' : self.uuid})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == 1:
            NewProjectReportThread(self).run()


class Segment(models.Model):
    tu_id = models.PositiveIntegerField()
    s_id = models.PositiveIntegerField()
    source = models.TextField(blank=True)
    target = models.TextField(blank=True)
    status = models.IntegerField(choices=segment_statuses, default=0)
    is_locked = models.BooleanField(default=False)
    file = models.ForeignKey(ProjectFile, models.CASCADE)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='segment_create')
    updated_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='segment_update')

    def get_status(self):
        return segment_statuses[self.status][1]

    def save(self, no_override=False, cur_target=None, cur_updated_by=None, *args, **kwargs):
        super().save(*args, **kwargs)
        prev_target = cur_target if cur_target is not None else self.target
        prev_updated_by = cur_updated_by if cur_updated_by is not None else self.updated_by
        if no_override:
            return
        elif self.target != '' and self.target != prev_target:
            try:
                Path('.tmp').mkdir(exist_ok=True)
                with tempfile.TemporaryDirectory(dir='.tmp') as tmpdir:
                    path_bf = Path(tmpdir, Path(self.file.bilingual_file.name).name)
                    path_bf.write_bytes(self.file.bilingual_file.read())

                    bf = open_bilingualfile(path_bf)

                bf.update_segment('<target>' + self.target + '</target>',
                                  self.tu_id,
                                  self.s_id,
                                  segment_state=('blank','draft','translated')[int(self.status)])
            except:
                self.target = prev_target
                self.updated_by = prev_updated_by
                self.save(no_override=True)
                raise ValueError('''Can't update the segment''')
            finally:
                segment_update = apps.get_model('kaplancloudapp', 'SegmentUpdate')()
                segment_update.source = self.source
                segment_update.target = self.target
                segment_update.status = self.status
                segment_update.segment = self
                if self.updated_by:
                    segment_update.submitted_by = self.updated_by
                elif self.created_by:
                    segment_update.submitted_by = self.created_by
                segment_update.save()


class SegmentUpdate(models.Model):
    source = models.TextField(blank=True)
    target = models.TextField(blank=True)
    status = models.IntegerField(choices=segment_statuses, default=1)
    segment = models.ForeignKey(Segment, models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)


class Comment(models.Model):
    comment = models.TextField()
    is_active = models.BooleanField(default=True)
    segment = models.ForeignKey(Segment, models.CASCADE)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
