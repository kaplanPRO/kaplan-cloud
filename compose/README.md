# Container deployment

A reference `compose` setup for running Kaplan Cloud in production with
Postgres, Gunicorn, and an Nginx static-files sidecar. For local
development, see the root [`README.md`](../README.md) instead.

## Prerequisites

- `podman` (or `docker`) with a compose plugin. The project's canonical
  command is `podman compose`; `docker compose` works identically.
- A reverse proxy in front of this stack to terminate TLS and route
  traffic to the `nginx` service. The compose file defaults to the
  network used by
  [`nginxproxy/nginx-proxy`](https://hub.docker.com/r/nginxproxy/nginx-proxy);
  override `NETWORK_NAME` in `.env` if you're using something else.

## Setup

From this directory:

```bash
cp .env.template .env             # fill in DB_NAME, DB_USER, DB_PASSWORD, etc.
cp .env.web.template .env.web     # set VIRTUAL_HOST
podman compose up -d
podman compose exec app python manage.py createsuperuser
```

The Postgres data directory and uploaded project files are bind-mounted
under `./db/data/db` and `./app/projects` respectively, so state persists
across container restarts and image upgrades.

## Inviting teammates

Sign in to `/admin` with the superuser account and create a
`UserRegistrationToken` for each new teammate. The token is shown once
and is single-use — share the registration URL
`https://<your-host>/accounts/register?token=<TOKEN>` with the recipient.
Permissions (translator, reviewer, PM) are assigned automatically based
on the user type chosen when the token was created.

Only admins and members of the `PM` group can create projects, clients,
translation memories, and language profiles.

## Links

- [`kaplanpro/cloud` on Docker Hub](https://hub.docker.com/r/kaplanpro/cloud)
- [kaplan.pro](https://kaplan.pro)
