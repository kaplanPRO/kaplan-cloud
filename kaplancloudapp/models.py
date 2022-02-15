from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from pathlib import Path

from .thread_classes import NewFileThread, NewProjectReportThread
from .utils import get_kpp_path, get_source_file_path, get_target_file_path
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

    def __str__(self):
        return str(self.id) + '-' + self.name


class Termbase(models.Model):
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
        return reverse('tm', kwargs={'id' : self.id})


class TMEntry(models.Model):
    source = models.TextField()
    target = models.TextField()
    translationmemory = models.ForeignKey(TranslationMemory, models.CASCADE)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='tmentry_create')
    updated_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='tmentry_update')
    updated_at = models.DateTimeField(auto_now=True)


class TMEntryUpdate(models.Model):
    source = models.TextField(blank=True)
    target = models.TextField(blank=True)
    tmentry = models.ForeignKey(TMEntry, models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)


class Project(models.Model):
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
    directory = models.TextField()
    due_by = models.DateTimeField(blank=True, null=True)
    _are_all_files_submitted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id) + '-' + self.name

    class Meta:
       ordering = ['-id']

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('project', kwargs={'id' : self.id})

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
    name = models.TextField()
    source_language = models.CharField(max_length=10)
    target_language = models.CharField(max_length=10)
    project = models.ForeignKey(Project, models.CASCADE)
    source_file = models.FileField(upload_to=get_source_file_path, blank=True, null=True)
    source_bilingualfile = models.FileField(upload_to=get_source_file_path, blank=True, null=True)
    target_bilingualfile = models.FileField(upload_to=get_target_file_path, blank=True)
    status = models.IntegerField(choices=project_statuses, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    due_by = models.DateTimeField(blank=True, null=True)
    translator = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='translator')
    reviewer = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='reviewer')

    def __str__(self):
        return '-'.join((str(self.project.id), str(self.id), self.name))

    class Meta:
       ordering = ['name']

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('editor', kwargs={'id' : self.id})

    def get_status(self):
        status_dict = dict(file_statuses)
        return status_dict[self.status]

    def get_target_directory(self):
        return str(Path(self.project.directory) / self.target_language)

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
    project = models.ForeignKey(Project, models.CASCADE)
    package = models.FileField(upload_to=get_kpp_path, max_length=255)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']


class ProjectReport(models.Model):
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
        return reverse('report', kwargs={'id' : self.id})

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
    file = models.ForeignKey(ProjectFile, models.CASCADE)
    created_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='segment_create')
    updated_by = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name='segment_update')

    @property
    def get_status(self):
        return segment_statuses[self.status][1]


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
