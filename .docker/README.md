## Example docker-compose configuration

Hello and thank you for giving Kaplan Cloud a try!

This example configuration assumes that you have [nginxproxy/nginx-proxy](https://hub.docker.com/r/nginxproxy/nginx-proxy) running on the same machine and connected to a docker network the name of which you will declare under NETWORK_NAME in the .env file. Below is an example .env file:

    POSTGRES_DB=postgres
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=postgres
    VIRTUAL_HOST=deneme.com.tr
    NETWORK_NAME=deneme

When you're done, run `docker-compose up -d` while in the same directory as docker-compose.yml

You'll need a superuser (admin) account.
```
docker-compose exec app python manage.py createsuperuser
```
Head to deneme.com.tr/admin (subsitute deneme.com.tr with the domain you
entered for VIRTUAL_HOST) to create accounts for teammates. The recommended way
to invite team members is to create a UserRegistrationToken which you'll find
on the left-hand side of the admin view. The invited team member then enters
their token at deneme.com.tr/accounts/register and their user permissions are
automatically assigned based on the user type you specified when creating the
token.

Please be advised that only admins, and users assigned to the PM group may
create projects and other resources.

### Links
1. [Kaplan Cloud docker repository](https://hub.docker.com/r/kaplanpro/cloud)
2. [Kaplan homepage](https://kaplan.pro)
