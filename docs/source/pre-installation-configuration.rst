Pre-Installation Configuration
==============================

File storage
------------

.. warning::
   You should not change the type of storage post-installation. Your files
   will not be moved to the new storage automatically. You'd need to copy
   them over manually.

-----
Local
-----
Local file storage does not require additional configuration. Static files,
which are needed for the app to function are stored at *$PROJECT_DIR/staticfiles*.
Project files, packages and others are stored at
*$PROJECT_DIR/kaplancloudapp/projects*.

--
S3
--
Kaplan Cloud depends on `django-storages <https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html>`_
to offer S3 support. You will need two S3 buckets, one with public access and
one without. The one with public access will store static files and the one
without will store project files, packages, etc.

1. Create the public bucket. Make sure to uncheck **Block all public access**.
You will set the environment variable ``S3_PUBLIC_BUCKET`` to the name of the
bucket, and ``S3_REGION_NAME`` to the bucket's region.

  .. image:: ./_static/img/aws-s3-create-public-bucket.png
    :alt: AWS S3 create public bucket

2. Edit the bucket's policy to allow anonymous read access. Change the entry
under **Resource** to the name of your bucket.

  .. image:: ./_static/img/aws-s3-public-bucket-policy.png
    :alt: AWS S3 edit public bucket policy

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
                  "arn:aws:s3:::kaplanclouddemo-public/*"
              ]
          }
      ]
    }

3. Create the private bucket. You will set the environment variable
``S3_PRIVATE_BUCKET`` to the name of this bucket.

  .. image:: ./_static/img/aws-s3-create-private-bucket.png
    :alt: AWS S3 create private bucket

4. Head over to IAM and create a policy with full access to these buckets. Change
``arn:aws:s3:::kaplanclouddemo-private`` and ``arn:aws:s3:::kaplanclouddemo-public``
to the names of your buckets.

  .. image:: ./_static/img/aws-iam-policy.png
    :alt: AWS IAM create policy

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
                  "arn:aws:s3:::kaplanclouddemo-private/*",
                  "arn:aws:s3:::kaplanclouddemo-private",
                  "arn:aws:s3:::kaplanclouddemo-public/*",
                  "arn:aws:s3:::kaplanclouddemo-public"
              ]
            }
        ]
    }

5. Under Users, create a user for **Access key - Programmatic access**.

  .. image:: ./_static/img/aws-iam-add-user.png
    :alt: AWS IAM create user

6. Click **Attach existing policies directly** and select the policy we
created at step 4.

  .. image:: ./_static/img/aws-iam-attach-existing-policies-directly.png
    :alt: AWS IAM attach policy

7. At the final step, you will be presented with your credentials. You'll set
the environment variable ``S3_ACCESS_KEY_ID`` to **Access key ID**, and
``S3_SECRET_ACCESS_KEY`` to **Secret access key**.

  .. image:: ./_static/img/aws-iam-credentials.png
    :alt: AWS IAM credentials

.. note::
   By default, static files will be saved under */static* in the public bucket,
   and project files will be saved under the root directory of the private
   bucket. You can change these directories by setting the environment variables
   ``S3_PUBLIC_BUCKET_LOCATION`` and ``S3_PRIVATE_BUCKET_LOCATION``
