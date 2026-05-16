## Example docker-compose configuration

Hello and thank you for giving Kaplan Cloud a try!

This example configuration assumes that you have
[nginxproxy/nginx-proxy](https://hub.docker.com/r/nginxproxy/nginx-proxy) and,
optionally, [nginxproxy/acme-companion](https://hub.docker.com/r/nginxproxy/acme-companion)
running on the same machine. Please make sure to connect the
nginxproxy/nginx-proxy container to a network, the name of which you'll need
to set to the NETWORK_NAME environment variable in .env. Please see the
.env.template and .env.web.template files for instructions.

When you're done, run `docker-compose up -d` while in the same directory as docker-compose.yml

You'll need a superuser (admin) account.
```
docker-compose exec app python manage.py createsuperuser
```
Head to subdomain.yourdomain.tld/admin (subsitute subdomain.yourdomain.tld with
the domain you entered for VIRTUAL_HOST) to create accounts for teammates. The
recommended way to invite team members is to create a UserRegistrationToken
which you'll find on the left-hand side of the admin view. The invited team
member then enters their token at deneme.com.tr/accounts/register and their
user permissions are automatically assigned based on the user type you
specified when creating the token.

Please be advised that only admins, and users assigned to the PM group may
create projects and other resources.

### Links
1. [Kaplan Cloud docker repository](https://hub.docker.com/r/kaplanpro/cloud)
2. [Kaplan homepage](https://kaplan.pro)
