from django.conf import settings
from django.contrib.staticfiles.storage import FileSystemStorage

def get_private_storage():
    if settings.DEFAULT_FILE_STORAGE == 'storages.backends.s3boto3.S3Boto3Storage':
        from storages.backends.s3boto3 import S3Boto3Storage


        class PrivateStorage(S3Boto3Storage):
            bucket_name = settings.S3_PRIVATE_BUCKET_NAME
            default_acl = None
            file_overwrite = False
            location = settings.S3_PRIVATE_BUCKET_LOCATION

        return PrivateStorage()
    elif settings.DEFAULT_FILE_STORAGE == 'storages.backends.gcloud.GoogleCloudStorage':
        from storages.backends.gcloud import GoogleCloudStorage


        class PrivateStorage(GoogleCloudStorage):
            bucket_name = settings.GS_PRIVATE_BUCKET_NAME
            default_acl = None
            file_overwrite = False
            location = settings.GS_PRIVATE_BUCKET_LOCATION

        return PrivateStorage()

    else:
        return FileSystemStorage()
