# Generated by Django 3.2.10 on 2021-12-16 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kaplancloudapp', '0003_auto_20211129_1211'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectreport',
            name='project_files',
            field=models.ManyToManyField(to='kaplancloudapp.ProjectFile'),
        ),
        migrations.AddField(
            model_name='projectreport',
            name='status',
            field=models.IntegerField(choices=[(0, 'Blank'), (1, 'Not Ready'), (2, 'Processing'), (3, 'Ready')], default=0),
        ),
    ]
