# Generated by Django 3.2.12 on 2022-03-14 08:43

from django.db import migrations

from kaplan import open_bilingualfile

from pathlib import Path
import tempfile

def remove_target_bilingualfile(apps, schema_editor):
    ProjectFile = apps.get_model('kaplancloudapp', 'ProjectFile')
    for project_file in ProjectFile.objects.all():
        project_file.target_bilingualfile.delete()

def prepare_target_bilingualfile(apps, schema_editor):
    ProjectFile = apps.get_model('kaplancloudapp', 'ProjectFile')
    Segment = apps.get_model('kaplancloudapp', 'Segment')
    Path('.tmp').mkdir(exist_ok=True)
    for project_file in ProjectFile.objects.all():
        with tempfile.TemporaryDirectory(dir='.tmp') as tmpdir:
            path_target_bf = Path(tmpdir, Path(project_file.source_bilingualfile.name).name)
            path_target_bf.write_bytes(project_file.source_bilingualfile.read())

            target_bf = open_bilingualfile(path_target_bf)

            for relevant_segment in Segment.objects.filter(file=project_file):
                target_bf.update_segment('<target>' + relevant_segment.target + '</target>',
                                         relevant_segment.tu_id,
                                         relevant_segment.s_id,
                                         segment_state=('blank','draft','translated')[int(relevant_segment.status)]
                                        )
            target_bf.save(tmpdir)

            with open(path_target_bf, 'rb') as target_bf:
                project_file.target_bilingualfile.save(path_target_bf.name,
                                                       target_bf)


class Migration(migrations.Migration):

    dependencies = [
        ('kaplancloudapp', '0009_alter_project_directory'),
    ]

    operations = [
        migrations.RunPython(
            remove_target_bilingualfile,
            prepare_target_bilingualfile
        ),
        migrations.RenameField(
            model_name='projectfile',
            old_name='source_bilingualfile',
            new_name='bilingual_file',
        ),
        migrations.RemoveField(
            model_name='projectfile',
            name='target_bilingualfile',
        ),

    ]