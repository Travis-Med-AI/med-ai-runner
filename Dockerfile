FROM docker:dind

FROM python:3.8

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

WORKDIR /
COPY Pipfile* ./
RUN pip install pipenv
RUN pipenv lock --requirements > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY ./app /app/

WORKDIR /app

