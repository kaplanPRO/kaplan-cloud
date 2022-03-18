Try for Free Online
===================

================================
Google Cloud Console Cloud Shell
================================

.. note::
   You may need to set up a project for this to work; however, you won't be
   asked for billing information, or charged. You will be using your weekly
   GCP Cloud Shell quota.

1. Head on over to https://console.cloud.google.com/ and click **Activate Cloud
Shell** at top right corner and wait for your Cloud Shell machine to be provisioned.

  .. image:: ./_static/img/gcp-cloud-shell.png
    :alt: Activate GCP Cloud Shell

2. Run a Kaplan Cloud container:

  .. image:: ./_static/img/gcp-cloud-shell-run-kaplan-cloud.png
    :alt: Run a Kaplan Cloud container

  .. code-block::

    docker run -d \
    -p 8080:8080 \
    -e CSRF_TRUSTED_ORIGINS=https://*.cloudshell.dev \
    --name kaplan-cloud-demo \
    kaplanpro/cloud

3. Create a superuser account:

  .. image:: ./_static/img/gcp-cloud-shell-createsuperuser.png
    :alt: Create a superuser account

  .. code-block::

    docker exec -it kaplan-cloud-demo python manage.py createsuperuser

4. Click **Web Preview** and then **Preview on port 8080**

  .. image:: ./_static/img/gcp-cloud-shell-web-preview-button.png
    :alt: Web Preview button

5. You should see the login page. You might need to give it a moment.

  .. image:: ./_static/img/gcp-cloud-shell-preview-login.png
    :alt: Web Preview login page

6. Log in with your credentials and give Kaplan Cloud a try!

  .. image:: ./_static/img/gcp-cloud-shell-preview-homepage.png
    :alt: Web Preview homepage page
