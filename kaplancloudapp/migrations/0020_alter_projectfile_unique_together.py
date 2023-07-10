# Generated by Django 4.2.2 on 2023-07-01 11:30

from django.db import migrations
import django.db.migrations.operations.special

from pathlib import Path

def change_nonunique_file_names_per_project(apps, schema_editor):
    Project = apps.get_model('kaplancloudapp', 'Project')
    ProjectFile = apps.get_model('kaplancloudapp', 'ProjectFile')

    for project in Project.objects.all():
        project_files = ProjectFile.objects.filter(project=project)
        if len(project_files) < 2:
            continue

        project_file_names = {}
        for project_file in project_files:
            project_file_names[project_file.name] = project_file_names.get(project_file.name, []) + [project_file.id]
        
        for name, ids in project_file_names.items():
            if len(ids) == 1:
                continue

            for i, id in enumerate(sorted(ids)[1:], start=1):
                name = Path(name)
                new_name = f'{name.stem}_{i}{"." if name.suffix.strip() != "" else ""}{name.suffix}'

                project_file = project_files.get(id=id)
                project_file.name = new_name
                project_file.save()


class Migration(migrations.Migration):

    dependencies = [
        ('kaplancloudapp', '0019_remove_projectfile_source_language_and_more'),
    ]

    operations = [
        migrations.RunPython(
            code=change_nonunique_file_names_per_project,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AlterUniqueTogether(
            name='projectfile',
            unique_together={('name', 'project')},
        ),
    ]