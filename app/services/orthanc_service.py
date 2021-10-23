import os
import shutil
import json
import traceback
from zipfile import ZipFile
from typing import List
import nvidia_smi
import glob
import requests
import redis
import docker
from medaimodels import ModelOutput
from settings import settings_service


def get_study(orthanc_id: str) -> (str, str, str, str, str):
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
    orthanc_url = settings_service.get_orthanc_url()
    series_url = f'{orthanc_url}/series/{orthanc_id}'
    series_info = requests.get(series_url).json()
    series_uid = series_info.get('MainDicomTags', {}).get('SeriesInstanceUID', '')
    description = series_info.get('MainDicomTags', {}).get('PerformedProcedureStepDescription', '')
    study_id = series_info['ParentStudy']

    study_info_url = f'{orthanc_url}/studies/{study_id}'
    study_info = requests.get(study_info_url).json()
    study_uid = study_info.get('MainDicomTags', {}).get('StudyInstanceUID', '')
    accession = study_info.get('MainDicomTags', {}).get('AccessionNumber', '')

    # extract the modality from the series
    modality = series_info.get('MainDicomTags', {}).get('Modality')

    # get a preview of the first instance in the series
    instance_id = list(series_info.get('Instances', {}))[0]
    study_png = requests.get(f'{orthanc_url}/instances/{instance_id[0]}/preview', stream=True)

    # define download path for study
    out_path = f'/opt/images/{orthanc_id}'
    png_path = f'{out_path}.png'

    study_file = open(png_path, 'wb')

    study_file.write(study_png.content)
    study_file.close()

    return orthanc_id, study_info.get('PatientMainDicomTags', {}).get('PatientID'), modality, study_uid, series_uid, accession, description

def get_modality(orthanc_id: str) -> str:
    """
    Gets the modality of an orthanc study by orthanc id

    Args:
        orthanc_id: the id of the study from orthanc

    Returns
        :str: the modality of the study
    """
    orthanc_url = settings_service.get_orthanc_url()
    preview_url = f'{orthanc_url}/series/{orthanc_id}'
    series_info = requests.get(preview_url).json()

    return series_info.get('MainDicomTags', {} ).get('Modality')


def get_orthanc_studies():
    """
    Retrieve orthanc study ids from orthanc

    Returns
        :obj:`list` of :obj:`int`: a list of the orhthan IDs
    """
    orthanc_url = settings_service.get_orthanc_url()
    url = f'{orthanc_url}/series'
    studies = requests.get(url)

    return studies.json()

def download_study_dicom(orthanc_id):
    """
    """
    orthanc_url = settings_service.get_orthanc_url()
    media_url = f'{orthanc_url}/series/{orthanc_id}/archive'
    print(f'downloading {orthanc_id} from orthanc using {media_url}')
    study = requests.get(media_url)
    out_path = f'/opt/images/{orthanc_id}'
    file_path = f'{out_path}.zip'
    # write the downloaded study to disk
    open(file_path, 'wb').write(study.content)
    print(f'writing to {file_path}')

    with ZipFile(file_path, 'r') as zip_obj:
        zip_obj.extractall(out_path)

def delete_study_dicom(orthanc_id):
    """
    """
    out_path = f'/opt/images/{orthanc_id}'
    file_path = f'{out_path}.zip'

    os.remove(file_path)
    shutil.rmtree(out_path, ignore_errors=True)

def delete_all_downloaded():
    """
    """
    fileList = glob.glob('/opt/images/*')
    # Iterate over the list of filepaths & remove each file.
    for filePath in fileList:
        try:
            shutil.rmtree(filePath, ignore_errors=True)
            os.remove(filePath)
        except:
            traceback.print_exc()
            print("Error while deleting file : ", filePath)

