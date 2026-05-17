#!/bin/bash

if [[ -z "${SECRET_KEY}" ]]; then
  echo "SECRET_KEY is unset. Generating it"
  export SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9&-@' | fold -w 62 | head -n 1)
fi

# Collect static files
echo "Collect static files"
python manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate --noinput

# Load PM group from fixtures
echo "Load PM group from fixtures"
python manage.py loaddata pm-group

# Start server
echo "Starting server"
if [[ "${USE_GUNICORN:-False}" = "True" ]]; then
  gunicorn kaplancloud.wsgi:application -b 0.0.0.0:${KAPLAN_PORT:-8080} -w ${GUNICORN_WORKERS:-2} -t ${GUNICORN_TIMEOUT:-300}
else
  python manage.py runserver 0.0.0.0:${KAPLAN_PORT:-8080}
fi
