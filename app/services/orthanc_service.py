import os
import shutil
import json
from zipfile import ZipFile
from typing import List
import nvidia_smi

import requests
import redis
import docker
from medaimodels import ModelOutput


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
    study_uid = study_info.get('MainDicomTags', {}).get('StudyInstanceUID', '')

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
    png_path = f'{out_path}.png'

    study_file = open(png_path, 'wb')

    study_file.write(study_png.content)
    study_file.close()

    return orthanc_id, study_info.get('PatientMainDicomTags', {}).get('PatientID'), modality, study_uid

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

def get_study_info(orthanc_id: str):
    study_info_url = f'http://orthanc:8042/studies/{orthanc_id}'
    study_info = requests.get(study_info_url).json()
    study_uid = study_info.get('MainDicomTags', {}).get('StudyInstanceUID', '')

    return orthanc_id, study_info.get('PatientMainDicomTags', {}).get('PatientID'), study_uid


def get_orthanc_studies():
    """
    Retrieve orthanc study ids from orthanc

    Returns
        :obj:`list` of :obj:`int`: a list of the orhthan IDs
    """

    url = 'http://orthanc:8042/studies'
    studies = requests.get(url)

    return studies.json()

def download_study_dicom(orthanc_id):
    """
    """
    print(f'downloading {orthanc_id} from orthanc')
    media_url = f'http://orthanc:8042/studies/{orthanc_id}/media'
    study = requests.get(media_url)
    out_path = f'/tmp/{orthanc_id}'
    file_path = f'{out_path}.zip'
    # write the downloaded study to disk
    open(file_path, 'wb').write(study.content)

    with ZipFile(file_path, 'r') as zip_obj:
        zip_obj.extractall(out_path)

def delete_study_dicom(orthanc_id):
    """
    """
    out_path = f'/tmp/{orthanc_id}'
    file_path = f'{out_path}.zip'

    os.remove(file_path)
    shutil.rmtree(out_path, ignore_errors=True)
