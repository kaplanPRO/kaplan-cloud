# Generated by Django 4.2.1 on 2023-05-21 13:09

from django.db import migrations, models
import django.db.migrations.operations.special
import uuid


def gen_uuid(apps, schema_editor, model_name):
    prev_uuids = []
    MyModel = apps.get_model('kaplancloudapp', model_name)
    for row in MyModel.objects.all():
        new_uuid = uuid.uuid4()
        while new_uuid in prev_uuids:
            print(new_uuid)
            new_uuid = uuid.uuid4()
        prev_uuids.append(new_uuid)
        row.uuid = new_uuid
        row.save(update_fields=['uuid'])

def gen_uuid_for_project(apps, schema_editor):
    gen_uuid(apps, schema_editor, 'project')

def gen_uuid_for_projectfile(apps, schema_editor):
    gen_uuid(apps, schema_editor, 'projectfile')

def gen_uuid_for_projectpackage(apps, schema_editor):
    gen_uuid(apps, schema_editor, 'projectpackage')

def gen_uuid_for_projectreferencefile(apps, schema_editor):
    gen_uuid(apps, schema_editor, 'projectreferencefile')

def gen_uuid_for_projectreport(apps, schema_editor):
    gen_uuid(apps, schema_editor, 'projectreport')

def gen_uuid_for_termbase(apps, schema_editor):
    gen_uuid(apps, schema_editor, 'termbase')

def gen_uuid_for_translationmemory(apps, schema_editor):
    gen_uuid(apps, schema_editor, 'translationmemory')


class Migration(migrations.Migration):

    replaces = [('kaplancloudapp', '0016_project_uuid_projectfile_uuid_projectpackage_uuid_and_more'), ('kaplancloudapp', '0017_generate_uuids'), ('kaplancloudapp', '0018_remove_null_uuids')]

    dependencies = [
        ('kaplancloudapp', '0015_client_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.AddField(
            model_name='projectfile',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.AddField(
            model_name='projectpackage',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.AddField(
            model_name='projectreferencefile',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.AddField(
            model_name='projectreport',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.AddField(
            model_name='termbase',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.AddField(
            model_name='translationmemory',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.RunPython(
            code=gen_uuid_for_project,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=gen_uuid_for_projectfile,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=gen_uuid_for_projectpackage,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=gen_uuid_for_projectreferencefile,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=gen_uuid_for_projectreport,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=gen_uuid_for_termbase,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=gen_uuid_for_translationmemory,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='project',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='projectfile',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='projectpackage',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='projectreferencefile',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='projectreport',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='termbase',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='translationmemory',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]