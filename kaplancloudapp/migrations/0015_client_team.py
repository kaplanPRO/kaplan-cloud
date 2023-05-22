# Generated by Django 4.2.1 on 2023-05-20 09:20

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('kaplancloudapp', '0014_projectpreprocessingsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='team',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]