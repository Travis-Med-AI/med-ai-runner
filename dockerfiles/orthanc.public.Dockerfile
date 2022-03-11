FROM jodogne/orthanc-plugins:1.10.0
COPY orthanc.public.json /etc/orthanc/orthanc.json
RUN rm -rf 