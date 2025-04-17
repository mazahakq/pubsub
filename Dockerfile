FROM python:3.10-slim-buster

WORKDIR /code

RUN pip install --no-cache-dir flask pika requests loguru prometheus_client waitress
