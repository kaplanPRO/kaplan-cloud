#!/bin/bash

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
if [[ -z "${USE_GUNICORN}" ]]; then
  python manage.py runserver 0.0.0.0:${VIRTUAL_PORT-8080}
else
  gunicorn kaplancloud.wsgi:application -b 0.0.0.0:${VIRTUAL_PORT-8080} -w ${GUNICORN_WORKERS-2} -t ${GUNICORN_TIMEOUT-300}
fi
