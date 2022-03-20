from django.conf import settings
from django.contrib.staticfiles.storage import FileSystemStorage

from storages.backends.s3boto3 import S3Boto3Storage

def get_private_storage():
    if settings.DEFAULT_FILE_STORAGE == 'storages.backends.s3boto3.S3Boto3Storage':
        class PrivateStorage(S3Boto3Storage):
            bucket_name = settings.S3_PRIVATE_BUCKET_NAME
            file_overwrite = False
            location = settings.S3_PRIVATE_BUCKET_LOCATION

        return PrivateStorage()
    else:
        return FileSystemStorage()
