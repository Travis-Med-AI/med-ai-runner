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
import db_queries


def getResult(r, study_id):
    """
    Retrieve Numpy array from Redis key

    :param r: redis connection
    :param n: redis key for the save array

    :return: the numpy array reteived from redis
    """
    path = r.get(study_id)
    return np.load(f'/tmp/{path}')


def get_image_results(orthanc_ids):
    return [f'/tmp/{orthanc_id}/output.jpg' for orthanc_id in orthanc_ids]


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

    study_info_url = f'http://orthanc:8042/studies/{orthanc_id}'
    media_url = f'http://orthanc:8042/studies/{orthanc_id}/media'
    study = requests.get(media_url)
    study_info = requests.get(study_info_url).json()

    # define download path for study
    out_path = f'/tmp/{orthanc_id}'
    file_path = f'{out_path}.zip'

    # write the downloaded study to disk
    open(file_path, 'wb').write(study.content)

    # unzip and save study
    with ZipFile(file_path, 'r') as zipObj:
        zipObj.extractall(out_path)
    
    return orthanc_id, study_info.get('PatientMainDicomTags', {} ).get('PatientID')


def evaluate(model_image, dicom_paths, eval_id, imgOutput=False):
    # get redis client
    r = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)
    print('eval info', model_image, dicom_paths, eval_id)

    # get docker client
    client = docker.from_env()

    # define volume for docker images. All downloaded images are linked in this docker volume
    # downloaded studies are mounted in contianers at /opt/images
    volumes = {
        'ai-images': {'bind': '/opt/images', 'mode': 'rw'}
    }

    filenames = ','.join(dicom_paths)
    
    # send eval to docker daemon and start container
    # set env variables
    # set runtime to nvidia so that it has a connection to the cuda runtime on host
    stdout = client.containers.run(image=model_image, 
                                   detach=False, 
                                   environment={'FILENAMES': filenames, 'ID': eval_id, 'SAVE_IMAGE': imgOutput}, 
                                   runtime='nvidia', 
                                   network='ai-network',
                                   volumes=volumes)

    out = getResult(r, eval_id)
    if imgOutput:
        return out, get_image_results(dicom_paths)
    return out, None