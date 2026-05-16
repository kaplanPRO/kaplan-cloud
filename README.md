# Kaplan Cloud

Kaplan Cloud is a cloud-based translation management system. It handles
translation projects, source and bilingual files, translation memories,
terminology databases, and team collaboration between project managers,
translators, and reviewers.

User-facing documentation is published at
<https://docs.kaplan.pro/projects/kaplan-cloud>.

## Quick start (local development)

Requires Python 3.12+ and [`uv`](https://docs.astral.sh/uv/). SQLite is
used by default, so no separate database setup is needed.

```bash
cp .env.example .env                        # then fill in SECRET_KEY
uv sync
python manage.py migrate
python manage.py runserver 0.0.0.0:8080
```

`.env.example` documents every environment variable `settings.py`
reads — uncomment the ones you need (Postgres, S3, GCS, etc.).

## Container deployment

A reference `podman compose` (or `docker compose`) stack lives in
[`compose/`](compose/README.md). It bundles Postgres, the Gunicorn app
server, and an Nginx static-files sidecar designed to sit behind an
external reverse proxy.

## Tests and linting

```bash
python manage.py test
ruff check .
ruff format .
```

CI runs `ruff check` and the full test suite on every PR.

## License

See [`LICENSE`](LICENSE).
