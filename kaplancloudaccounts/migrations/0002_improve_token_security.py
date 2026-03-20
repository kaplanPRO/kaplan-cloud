from django.db import migrations, models
from django.utils import timezone

import kaplancloudaccounts.utils


def backfill_created_at(apps, schema_editor):
    UserRegistrationToken = apps.get_model(
        "kaplancloudaccounts", "UserRegistrationToken"
    )
    UserRegistrationToken.objects.filter(created_at__isnull=True).update(
        created_at=timezone.now()
    )


class Migration(migrations.Migration):
    dependencies = [
        ("kaplancloudaccounts", "0001_userregistrationtoken"),
    ]

    operations = [
        # Increase token max_length and update default
        migrations.AlterField(
            model_name="userregistrationtoken",
            name="token",
            field=models.CharField(
                default=kaplancloudaccounts.utils.generate_random_token,
                max_length=64,
                unique=True,
            ),
        ),
        # Add created_at as nullable first
        migrations.AddField(
            model_name="userregistrationtoken",
            name="created_at",
            field=models.DateTimeField(null=True),
        ),
        # Backfill existing rows
        migrations.RunPython(backfill_created_at, migrations.RunPython.noop),
        # Now make it non-nullable with auto_now_add
        migrations.AlterField(
            model_name="userregistrationtoken",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
