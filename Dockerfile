FROM python:3.8

ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY . /code/

RUN pip install -U pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]

RUN groupadd -r kaplan && useradd --no-log-init -r -g kaplan kaplan

RUN chown -R kaplan /code/

USER kaplan

EXPOSE 8080

STOPSIGNAL SIGINT
