"""Utils for the med ai runner"""

import os
import shutil
import json
from zipfile import ZipFile
from typing import List

import requests
import redis
import docker
from medaimodels import ModelOutput


def get_result(redis_connection, eval_id: int) -> ModelOutput:
    """
    Retrieve Numpy array from Redis key

    Args:
        redis_connection (:obj): the redis connection
        study_id (int): the ID of the study

    Returns
        :obj:`ModelOutput`: the output received from redis
    """
    output = redis_connection.get(eval_id)
    return json.loads(output)


def get_orthanc_studies():
    """
    Retrieve orthanc study ids from orthanc

    Returns
        :obj:`list` of :obj:`int`: a list of the orhthan IDs
    """

    url = 'http://orthanc:8042/studies'
    studies = requests.get(url)

    return studies.json()


def get_study(orthanc_id: str) -> (str, str, str):
    """
    Retreive study from orthanc

    Args:
        orthanc_id (str): the study ID for orthanc

    Returns
        :rtype: (str, str, str)
    """

    # get study info from orthanc
    study_info_url = f'http://orthanc:8042/studies/{orthanc_id}'
    study_info = requests.get(study_info_url).json()

    # download the dicom from orthanc
    media_url = f'http://orthanc:8042/studies/{orthanc_id}/media'
    study = requests.get(media_url)

    # get the dicom's series ID from study metadata
    series_id = list(study_info.get('Series', {}))[0]

    # download the series metadata from orthanc
    series_url = f'http://orthanc:8042/series/{series_id}'
    series_info = requests.get(series_url).json()

    # extract the modality from the series
    modality = series_info.get('MainDicomTags', {}).get('Modality')

    # get a preview of the first instance in the series
    instance_id = list(series_info.get('Instances', {}))[0]
    study_png = requests.get(f'http://orthanc:8042/instances/{instance_id[0]}/preview', stream=True)

    # define download path for study
    out_path = f'/tmp/{orthanc_id}'
    file_path = f'{out_path}.zip'
    png_path = f'{out_path}.png'

    # write the downloaded study to disk
    open(file_path, 'wb').write(study.content)

    with open(png_path, 'wb') as file:
        study_png.raw.decode_content = True
        shutil.copyfileobj(study_png.raw, file)

    # unzip and save study
    with ZipFile(file_path, 'r') as zip_obj:
        zip_obj.extractall(out_path)

    return orthanc_id, study_info.get('PatientMainDicomTags', {}).get('PatientID'), modality


def evaluate(model_image: str, dicom_paths: List[str], eval_id: int) -> List[ModelOutput]:
    """
    Evaluate a study using a model

    Args:
        model_image (str): the tag of the docker that contains the model
        dicom_paths (List[str]): a list of the paths of the dicoms to be evalutated
        eval_id (int): the db ID of the evaluation

    Returns
        :rtype: List[ModelOutput]
        A list of the outputs of the evaluating model
    """
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
    client.containers.run(image=model_image, 
                          detach=False, 
                          environment={'FILENAMES': filenames, 'ID': eval_id}, 
                          runtime='nvidia', 
                          network='ai-network',
                          volumes=volumes,
                          shm_size='11G')

    out = get_result(r, eval_id)
    return out


def get_modality(orthanc_id: str) -> str:
    """
    Gets the modality of an orthanc study by orthanc id

    Args:
        orthanc_id: the id of the study from orthanc

    Returns
        :str: the modality of the study
    """
    study_info_url = f'http://orthanc:8042/studies/{orthanc_id}'
    study_info = requests.get(study_info_url).json()

    series_id = list(study_info.get('Series', {} ))
    preview_url = f'http://orthanc:8042/series/{series_id[0]}'
    series_info = requests.get(preview_url).json()

    return series_info.get('MainDicomTags', {} ).get('Modality')


def check_for_ct(orthanc_id: str) -> bool:
    """
    Checks to see if a study from orthanc is a CT scan or not
    by seeing if there are multiple slices in the dicomdir

    Args:
        orthanc_id (str): the study id of the study from orthanc
    Returns:
        :bool: a boolean of whether or not it is a CT scan
    """
    # Check to see if the dicomdir has multiple images
    path = f'/tmp/{orthanc_id}/IMAGES'
    return len(os.listdir(path)) > 1
