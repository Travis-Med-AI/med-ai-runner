FROM continuumio/miniconda3


ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

WORKDIR /
RUN apt-get update && apt-get install python3-gdcm libpq-dev build-essential -y
COPY requirements.txt ./
RUN conda install gdcm -c conda-forge
RUN pip install -r requirements.txt
RUN rm requirements.txt

COPY ./app /app/

WORKDIR /app
