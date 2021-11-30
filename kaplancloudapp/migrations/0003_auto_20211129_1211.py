# Generated by Django 3.2.6 on 2021-11-29 12:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import kaplancloudapp.utils


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('kaplancloudapp', '0002_projectreport'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='projectreport',
            options={'ordering': ['-id']},
        ),
        migrations.CreateModel(
            name='ProjectPackage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('package', models.FileField(max_length=255, upload_to=kaplancloudapp.utils.get_kpp_path)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kaplancloudapp.project')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
    ]
