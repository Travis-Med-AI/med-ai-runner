import os
from celery import Celery, shared_task
import settings
import docker
import redis
import numpy as np
import struct
from psycopg2 import connect
from psycopg2.extras import DictCursor
import time
from functools import reduce
import requests
from zipfile import ZipFile


def fromRedis(r,n):
   """
   Retrieve Numpy array from Redis key

   :param r: redis connection
   :param n: redis key for the save array

   :return: the numpy array reteived from redis
   """
   encoded = r.get(n)
   h, w = struct.unpack('>II',encoded[:8])
   a = np.frombuffer(encoded, dtype=np.float, offset=8).reshape(h,w)

   return a


def get_string_from_redis(r, key):
    return r.get(key)


def get_orthanc_studies():
    url = f'http://orthanc:8042/studies'
    studies = requests.get(url)

    return studies.json()


def get_study(orthanc_id):
    """
    Retreive study from orthanc, saves zip file to disk and unzips to directory

    :param orthanc_id: study id from orthanc
    """
    # get study zip from orthanc
    url = f'http://orthanc:8042/studies/{orthanc_id}/media'
    study = requests.get(url)

    # define download path for study
    out_path = f'/tmp/{orthanc_id}'
    file_path = f'{out_path}.zip'

    # write the downloaded study to disk
    open(file_path, 'wb').write(study.content)

    # unzip and save study
    with ZipFile(file_path, 'r') as zipObj:
        zipObj.extractall(out_path)
    
    return orthanc_id




def evaluate(model_image, dicom_path, id, stringOutput=False):
    # get redis client
    if stringOutput:
        r = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)
    else:
        r = redis.Redis(host='redis', port=6379, db=0)

    # get docker client
    client = docker.from_env()

    # define volume for docker images. All downloaded images are linked in this docker volume
    # downloaded studies are mounted in contianers at /opt/images
    volumes = {
        'ai-images': {'bind': '/opt/images', 'mode': 'rw'}
    }
    
    # send eval to docker daemon and start container
    # set env variables
    # set runtime to nvidia so that it has a connection to the cuda runtime on host
    stdout = client.containers.run(image=model_image, 
                                   detach=False, 
                                   environment={'FILENAME': dicom_path, 'ID': id}, 
                                   runtime='nvidia', 
                                   network='ai-network',
                                   volumes=volumes)


    # retreive output of container from redis and return
    if stringOutput:
        return get_string_from_redis(r, id)
    out = fromRedis(r, id)
    return out
