# Kaplan Cloud

A Django-based cloud translation management system. Manages translation projects, files, translation memories, terminology databases, and team collaboration.

## Apps

- `kaplancloudapp/` — core: projects, files, language profiles, translation memories, termbases
- `kaplancloudaccounts/` — user authentication and registration tokens
- `kaplancloudapi/` — REST API (DRF) with webhooks

## Development setup

Local dev uses SQLite by default — no database setup needed.

```bash
uv sync                                     # or: pip install --group dev
python manage.py migrate
python manage.py runserver 0.0.0.0:8080
```

For container-based dev use **podman compose** (not `docker compose`):

```bash
cd .docker
cp .env.template .env && cp .env.web.template .env.web
podman compose up -d
podman compose exec app python manage.py createsuperuser
```

## Common commands

```bash
python manage.py runserver 0.0.0.0:8080   # dev server
python manage.py migrate --noinput         # apply migrations
python manage.py test                      # run tests
python manage.py createsuperuser           # create admin user
python manage.py loaddata pm-group         # load PM group fixture
ruff check .                               # lint
ruff format .                              # format
```

## Code style

Use **ruff** for linting and formatting. No other formatters.

## Testing

New features and bug fixes should include tests. Test files live alongside each app:

- `kaplancloudapp/tests.py`
- `kaplancloudapi/tests.py`
- `kaplancloudaccounts/tests.py`

Run all tests with `python manage.py test`.

## Sensitive areas

- **kaplan library integration** — `kaplancloudapp/` models and views call the `kaplan` package for translation processing. Changes here can break core functionality; test thoroughly before modifying.
- **REST API backwards compatibility** — `kaplancloudapi/` serializers and endpoints may be consumed by external clients. Avoid removing or renaming fields; prefer additive changes.
