FROM continuumio/anaconda3


ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

WORKDIR /
COPY environment.yml ./
RUN conda env create -f environment.yml
RUN echo "source activate med-ai-runner" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH
COPY ./app /app/

WORKDIR /app
