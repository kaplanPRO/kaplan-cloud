FROM python:3.8
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY . /code/
RUN pip install -U pip
RUN pip install -r requirements.txt
RUN pip install gunicorn
