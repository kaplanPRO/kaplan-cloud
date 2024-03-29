FROM python:3.11

ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY . /code/

RUN apt-get update && \
    apt-get install -y postgresql-client

RUN pip install -U pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]

EXPOSE 8080

STOPSIGNAL SIGINT
