# Kaplan Cloud

Kaplan Cloud is a cloud-based translation management system.

The official documentation is available at https://docs.kaplan.pro/projects/kaplan-cloud

## Local installation with Docker

Please see [here](https://docs.kaplan.pro/projects/kaplan-cloud/en/latest/installation.html#local-installation-with-docker)
for instructions; however, for testing purposes, all you need to do is first
start a [Kaplan Cloud container](https://hub.docker.com/r/kaplanpro/cloud):

```
docker run -d \
-p 8080:8080 \
--restart always \
--name kaplan-cloud \
kaplanpro/cloud
```

And then create a superuser account:

```
docker exec -it kaplan-cloud python manage.py createsuperuser
```

That's it! Head on over to http://0.0.0.0:8080 and explore Kaplan Cloud.

## Production installation with Docker Compose

Please see [here](https://docs.kaplan.pro/projects/kaplan-cloud/en/latest/installation.html#production-installation-with-docker-compose)
for instructions.
