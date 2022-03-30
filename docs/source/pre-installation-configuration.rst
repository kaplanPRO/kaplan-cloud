Pre-Installation Configuration
==============================

File storage
------------

.. warning::
   You should not change the type of storage post-installation. Your files
   will not be moved to the new storage automatically. You'd need to copy
   them over manually.

.. note::
   For the purposes of this documentation, private content refers to project
   files, packages, etc. while public content refers to the style and logic
   files (CSS, JS, etc.) required for Kaplan Cloud to function in users' web
   browsers.

-----
Local
-----
Local file storage does not require additional configuration. Static files,
which are needed for the app to function are stored at *$PROJECT_DIR/staticfiles*.
Project files, packages and others are stored at
*$PROJECT_DIR/kaplancloudapp/projects*.

--------------------
Google Cloud Storage
--------------------

.. _Create a new bucket: https://cloud.google.com/storage/docs/creating-buckets#create_a_new_bucket
.. _Choose between uniform and fine-grained access: https://cloud.google.com/storage/docs/access-control#choose_between_uniform_and_fine-grained_access
.. _Creating a Service Account: https://cloud.google.com/docs/authentication/getting-started#creating_a_service_account

.. note::
   Kaplan Cloud depends on `django-storages
   <https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html>`_
   to offer Google Cloud Storage support.

1. Create a bucket (`Create a new bucket`_)
   and make sure to set control to *Fine-grained* (`Choose between uniform and
   fine-grained access`_). You will set the environment variables
   ``GS_PUBLIC_BUCKET_NAME`` and ``GS_PRIVATE_BUCKET_NAME`` to the name of this
   bucket.

2. Create a service account and make sure it has read and write access to your
   bucket (`Creating a Service Account`_).

3. Create and download an access key for your service account. You will set the
   environment variable ``GOOGLE_APPLICATION_CREDENTIALS`` to the path to this
   key file.

.. note::
   By default, public content will be saved under the */static* directory, while
   private content will be saved under the */kaplancloudapp/projects* directory.
   You can change these directories by setting the environment variables
   ``GS_PUBLIC_BUCKET_LOCATION`` and ``GS_PRIVATE_BUCKET_LOCATION``

--
S3
--

.. _Creating a bucket: https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html
.. _Using bucket policies: https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policies.html
.. _AWS IAM Docs: https://docs.aws.amazon.com/iam
.. _Creating IAM users: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html#id_users_create_console

.. note::
   Kaplan Cloud depends on `django-storages
   <https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html>`_
   to offer S3 support.

Separate buckets for private and public content (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create the public bucket (`Creating a bucket`_). Make sure to uncheck
   **Block all public access**. You will set the environment variable
   ``S3_PUBLIC_BUCKET`` to the name of the bucket, and ``S3_REGION_NAME`` to the
   bucket's region.

   .. note::
      For your public content to be actually public, you'll need to set the
      environment variable ``GS_DEFAULT_ACL`` to ``public-read``. This will not
      affect your private content.

2. Edit the bucket's policy to allow anonymous read access
   (`Using bucket policies`_). Below is a policy example, change
   ``mypublicbucket`` to the name of your bucket:

   .. code-block::

     {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Sid": "PublicRead",
               "Effect": "Allow",
               "Principal": "*",
               "Action": [
                   "s3:GetObject",
                   "s3:GetObjectVersion"
               ],
               "Resource": [
                   "arn:aws:s3:::mypublicbucket/*"
               ]
           }
       ]
     }

3. Create the private bucket (`Creating a bucket`_). You will set the
   environment variable ``S3_PRIVATE_BUCKET`` to the name of this bucket.

4. Head over to IAM and create a policy with full access to these buckets.
   Change ``arn:aws:s3:::myprivatebucket`` and ``arn:aws:s3:::mypublicbucket``
   to the names of your buckets (`AWS IAM Docs`_).

   .. code-block::

     {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Sid": "KaplanCloudBuckets",
               "Effect": "Allow",
               "Action": [
                   "s3:PutObject",
                   "s3:GetObjectAcl",
                   "s3:GetObject",
                   "s3:ListBucket",
                   "s3:DeleteObject",
                   "s3:PutObjectAcl"
               ],
               "Resource": [
                   "arn:aws:s3:::myprivatebucket/*",
                   "arn:aws:s3:::myprivatebucket",
                   "arn:aws:s3:::mypublicbucket/*",
                   "arn:aws:s3:::mypublicbucket"
               ]
             }
         ]
     }

5. Under Users, create a user for **Access key - Programmatic access** and
   attach the policy we created at the previous step (`Creating IAM users`_).

6. At the final step, you will be presented with your credentials. You'll set
   the environment variable ``S3_ACCESS_KEY_ID`` to **Access key ID**, and
   ``S3_SECRET_ACCESS_KEY`` to **Secret access key**.

.. note::
   By default, static files will be saved under */static* in the public bucket,
   and project files will be saved under the root directory of the private
   bucket. You can change these directories by setting the environment variables
   ``S3_PUBLIC_BUCKET_LOCATION`` and ``S3_PRIVATE_BUCKET_LOCATION``

Single bucket
~~~~~~~~~~~~~

1. Create a new bucket with ACL enabled and Block all public access unticked
   (`Creating a bucket`_). You will set the environment variables
   ``S3_PRIVATE_BUCKET`` and ``S3_PUBLIC_BUCKET`` to the name of this bucket.

   .. note::
      For your public content to be actually public, you'll need to set the
      environment variable ``S3_DEFAULT_ACL`` to ``public-read``. This will not
      affect your private content.

2. Head over to IAM and create a policy with full access to these buckets.
   Change ``arn:aws:s3:::mybucket`` to the name of your bucket (`AWS IAM Docs`_).

   .. code-block::

     {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Sid": "KaplanCloudBucket",
               "Effect": "Allow",
               "Action": [
                   "s3:PutObject",
                   "s3:GetObjectAcl",
                   "s3:GetObject",
                   "s3:ListBucket",
                   "s3:DeleteObject",
                   "s3:PutObjectAcl"
               ],
               "Resource": [
                   "arn:aws:s3:::mybucket/*",
                   "arn:aws:s3:::mybucket"
               ]
             }
         ]
     }

3. Under Users, create a user for **Access key - Programmatic access** and
   attach the policy we created at the previous step (`Creating IAM users`_).

4. At the final step, you will be presented with your credentials. You'll set
   the environment variable ``S3_ACCESS_KEY_ID`` to **Access key ID**, and
   ``S3_SECRET_ACCESS_KEY`` to **Secret access key**.

.. note::
   By default, public content will be saved under the */static* directory, while
   private content will be saved under the */kaplancloudapp/projects* directory.
   You can change these directories by setting the environment variables
   ``S3_PUBLIC_BUCKET_LOCATION`` and ``S3_PRIVATE_BUCKET_LOCATION``
