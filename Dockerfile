FROM python:3.8

ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY . /code/

RUN pip install -U pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]

EXPOSE 8080

STOPSIGNAL SIGINT
