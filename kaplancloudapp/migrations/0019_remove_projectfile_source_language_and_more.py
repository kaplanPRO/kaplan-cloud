# Generated by Django 4.2.2 on 2023-07-01 11:03

from django.db import migrations, models
import django.db.migrations.operations.special

def get_languages_from_project(apps, schema_editor):
    for project_file in apps.get_model('kaplancloudapp', 'ProjectFile').objects.all():
        project_file.source_language = project_file.project.source_language.iso_code
        project_file.target_language = project_file.project.target_language.iso_code
        project_file.save()

class Migration(migrations.Migration):

    dependencies = [
        ('kaplancloudapp', '0018_project_language_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectfile',
            name='source_language',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='projectfile',
            name='target_language',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.RunPython(
            code=django.db.migrations.operations.special.RunPython.noop,
            reverse_code=get_languages_from_project,
        ),
        migrations.RemoveField(
            model_name='projectfile',
            name='source_language',
        ),
        migrations.RemoveField(
            model_name='projectfile',
            name='target_language',
        ),
    ]
