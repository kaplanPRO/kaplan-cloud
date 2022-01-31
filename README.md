# Kaplan Cloud

Hello and thank you for giving Kaplan Cloud a try!

If you would like help getting set up or try the demo available at [clouddemo.kaplan.pro](https://clouddemo.kaplan.pro), please reach out to contact@kaplan.pro.

## Deploy with Docker locally

First, we need a [Postgres container](https://hub.docker.com/_/postgres) up and running:

```
docker run -d --expose 5432 -e POSTGRES_PASSWORD=postgres -v kaplan-postgres:/var/lib/postgresql/data --restart always --name kaplan-postgres postgres
```

Now, let's start a [Kaplan Cloud container](https://hub.docker.com/r/kaplanpro/cloud):

```
docker run -d -p 8080:8080 --link kaplan-postgres -e POSTGRES_HOST=kaplan-postgres -e POSTGRES_PASSWORD=postgres -v kaplan-cloud:/code/kaplancloudapp/projects --restart always --name kaplan-cloud kaplanpro/cloud
```

Finally, we need to create a superuser (admin):
```
docker exec -it kaplan-cloud python manage.py createsuperuser
```

We're done! Head on over to http://0.0.0.0:8080 and explore Kaplan Cloud.

## Deploy with Docker Compose in a production environment

There is a sample Docker Compose configuration available [here](https://github.com/kaplanPRO/kaplan-cloud/tree/main/.docker).
