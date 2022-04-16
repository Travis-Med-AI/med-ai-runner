from ast import Or
from operator import mod
import os
import shutil
import json
import traceback
from zipfile import ZipFile
from typing import Dict, List, NamedTuple
from db import study_db
import nvidia_smi
import glob
import requests
from requests import Response
import redis
import docker
from medaimodels import ModelOutput
from settings import settings_service
from dataclasses import dataclass

class OrthancMetadata(NamedTuple):
    orthanc_id: str
    patient_id: str
    modality: str
    study_uid: str
    series_uid: str
    accession:str
    description: str
    series_instances: List
    series_metadta: Dict
    study_metadta: Dict
    parent_orthanc_id: str

def download_metadata(orthanc_id: str):
    # Get orthanc url from setting
    orthanc_url = settings_service.get_orthanc_url()

    # Get relevant data from series metadata
    series_url = f'{orthanc_url}/series/{orthanc_id}'
    series_info = requests.get(series_url).json()
    main_series_tags = series_info.get('MainDicomTags', {})
    series_uid = main_series_tags.get('SeriesInstanceUID', '')
    description = main_series_tags.get('PerformedProcedureStepDescription', '')
    modality = main_series_tags.get('Modality')
    study_id = series_info['ParentStudy']
    instances = list(series_info.get('Instances', {}))

    # Get relevant data from stuudy metadata
    study_info_url = f'{orthanc_url}/studies/{study_id}'
    study_info = requests.get(study_info_url).json()
    main_study_metadata = study_info.get('MainDicomTags', {})
    study_uid = main_study_metadata.get('StudyInstanceUID', '')
    accession = main_study_metadata.get('AccessionNumber', '')
    patient_id = main_study_metadata.get('PatientID', '')

    return OrthancMetadata(
        orthanc_id=orthanc_id,
        patient_id = patient_id,
        modality=modality,
        study_uid=study_uid,
        series_uid=series_uid,
        accession=accession,
        description=description,
        series_instances=instances,
        series_metadta=main_series_tags,
        study_metadta=main_study_metadata,
        parent_orthanc_id=study_id
    )   


def save_series_preview(metadata: OrthancMetadata):
    # Get orthanc url from setting
    orthanc_url = settings_service.get_orthanc_url()
    # get a preview of the first instance in the series
    first_instance_id = metadata.series_instances[0]
    study_png = requests.get(f'{orthanc_url}/instances/{first_instance_id[0]}/preview', stream=True)

    # define download path for study
    out_path = f'/opt/images/{metadata.orthanc_id}'
    png_path = f'{out_path}.png'

    study_file = open(png_path, 'wb')

    study_file.write(study_png.content)
    study_file.close()
    

def get_study_metadata(orthanc_id: str) -> OrthancMetadata:
    """
    Retreive study from orthanc

    Args:
        orthanc_id (str): the study ID for orthanc

    Returns
        :OrthancMetadata
    """

    # get study info from orthanc
    metadata = download_metadata(orthanc_id)

    save_series_preview(metadata)

    return metadata

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


def get_orthanc_study_ids():
    """
    Retrieve orthanc study ids from orthanc

    Returns
        :obj:`list` of :obj:`int`: a list of the orhthan IDs
    """
    orthanc_url = settings_service.get_orthanc_url()
    url = f'{orthanc_url}/series'
    studies = requests.get(url)

    return studies.json()

def download_study_dicom(orthanc_id: str):
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

def delete_study_dicom(orthanc_id: str):
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

def delete_from_orthanc(orthanc_ids: List[str]):
    orthanc_url = settings_service.get_orthanc_url()
    bulk_delete_url = f'{orthanc_url}/tools/bulk-delete'
    body = {"Resources": orthanc_ids}
    print('posting with body ', json.dumps(body))
    res: Response = requests.post(bulk_delete_url, data=json.dumps(body))
    print(res)
    if res.status_code == 200:
        for o in orthanc_ids:
            study_db.save_deleted_orthanc(o)


