Installation
============

==============================
Local installation with Docker
==============================
1. Follow `these instructions <https://docs.docker.com/get-docker>`_ to install Docker.

2. Deploy a `Postgres container <https://hub.docker.com/_/postgres>`_:

    .. code-block::

        docker run -d \
        --expose 5432 \
        -e POSTGRES_PASSWORD=postgres \
        -v kaplan-postgres:/var/lib/postgresql/data \
        --restart always \
        --name kaplan-postgres \
        postgres

    "postgres" is your password for the Postgres instance. It'd be best to change it.

3. Deploy a `Kaplan Cloud container <https://hub.docker.com/r/kaplanpro/cloud>`_:

    .. code-block::

        docker run -d \
        -p 8080:8080 \
        --link kaplan-postgres \
        -e POSTGRES_HOST=kaplan-postgres \
        -e POSTGRES_PASSWORD=postgres \
        -v kaplan-cloud:/code/kaplancloudapp/projects \
        --restart always \
        --name kaplan-cloud \
        kaplanpro/cloud``

    Change "postgres" to the password you input in the previous step.

4. Create an admin (superuser) account:

    .. code-block::

        docker exec -it kaplan-cloud python manage.py createsuperuser

5. We're done! Head on over to http://0.0.0.0:8080 and explore Kaplan Cloud.

===========================================
Production installation with Docker Compose
===========================================

1. Follow `these instructions <https://docs.docker.com/get-docker>`_ to install Docker.

2. Follow `these instructions <https://docs.docker.com/compose/install>`_ to install Docker Compose.

3. If you have not set a dedicated Docker network for your proxy tier, create one:

  .. code-block::

      docker network create network-name

  Replace "network-name" with an arbitrary name of your choosing.

4. If you do not already have one, deploy an `nginxproxy/nginx-proxy container <https://hub.docker.com/r/nginxproxy/nginx-proxy>`_:

  .. code-block::

      docker run --detach \
      --name nginx-proxy \
      --network network-name \
      --publish 80:80 \
      --publish 443:443 \
      --volume certs:/etc/nginx/certs \
      --volume vhost:/etc/nginx/vhost.d \
      --volume html:/usr/share/nginx/html \
      --volume /var/run/docker.sock:/tmp/docker.sock:ro \
      --restart unless-stopped \
      nginxproxy/nginx-proxy

  This container will be routing traffic to your Kaplan Cloud instance.

5. If you do not already have one, deploy an `nginxproxy/acme-companion container <https://hub.docker.com/r/nginxproxy/acme-companion>`_:

  .. code-block::

      docker run --detach \
      --name nginx-proxy-acme \
      --volumes-from nginx-proxy \
      --volume /var/run/docker.sock:/var/run/docker.sock:ro \
      --volume acme:/etc/acme.sh \
      --env "DEFAULT_EMAIL=mail@yourdomain.tld" \
      --restart unless-stopped \
      nginxproxy/acme-companion

  This container will be provisioning free SSL certificates for your Kaplan Cloud instance.

6. Download the repository from here and enter the .docker directory.

7. You will find three \*.env.template files. Create .env, db.env and web.env files following the guidance on the templates.

8. Use docker-compose to run the containers::

      docker-compose up -d

  If, for some reason, this step fails, run this command without the -d flag to see what went wrong::

      docker-compose up

9. Create an admin (superuser) account::

    docker-compose exec app python manage.py createsuperuser

--------------------------------------
Additional steps for Cloudflare users
--------------------------------------

1. Add the following page rule:

  .. code-block::

      For: *yourdomain.tld/.well-known/*
      With: Disable Security, Cache Level: Bypass, Automatic HTTPS Rewrites: Off

  It might take a minute or two for the SSL certificate to kick in.
