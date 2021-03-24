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


def get_study(orthanc_id: str) -> (str, str, str, str):
    """
    Retreive study from orthanc

    Args:
        orthanc_id (str): the study ID for orthanc

    Returns
        :rtype: (str, str, str)
    """

    # get study info from orthanc


    # get the dicom's series ID from study metadata

    # download the series metadata from orthanc
    series_url = f'http://orthanc:8042/series/{orthanc_id}'
    series_info = requests.get(series_url).json()
    series_uid = series_info.get('MainDicomTags', {}).get('SeriesInstanceUID', '')

    study_id = series_info['ParentStudy']

    study_info_url = f'http://orthanc:8042/studies/{study_id}'
    study_info = requests.get(study_info_url).json()
    study_uid = study_info.get('MainDicomTags', {}).get('StudyInstanceUID', '')

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

    return orthanc_id, study_info.get('PatientMainDicomTags', {}).get('PatientID'), modality, study_uid, series_uid

def get_modality(orthanc_id: str) -> str:
    """
    Gets the modality of an orthanc study by orthanc id

    Args:
        orthanc_id: the id of the study from orthanc

    Returns
        :str: the modality of the study
    """
    preview_url = f'http://orthanc:8042/series/{orthanc_id}'
    series_info = requests.get(preview_url).json()

    return series_info.get('MainDicomTags', {} ).get('Modality')


def get_orthanc_studies():
    """
    Retrieve orthanc study ids from orthanc

    Returns
        :obj:`list` of :obj:`int`: a list of the orhthan IDs
    """

    url = 'http://orthanc:8042/series'
    studies = requests.get(url)

    return studies.json()

def download_study_dicom(orthanc_id):
    """
    """
    media_url = f'http://orthanc:8042/series/{orthanc_id}/archive'
    print(f'downloading {orthanc_id} from orthanc using {media_url}')
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
