"""Database queries used by med-ai runner"""

import json
from typing import List, Dict

from medaimodels import ModelOutput

from utils.db_utils import query_and_fetchall, query_and_fetchone, query, join_for_in_clause
from services import logger_service, messaging_service
from db import model_db


def get_study_by_orthanc_id(orthanc_id: str):
    """
    Gets a study by orthanc_id
    Args:
        orthanc_id (str): the orthanc_study
    Returns:
        Dict: the default classifier model
    """
    logger_service.log(f'inserting study for orthanc Id: {orthanc_id}')
    sql = f'''
    SELECT * from study
    WHERE "orthancStudyId"='{orthanc_id}'
    '''

    return query_and_fetchone(sql)

def get_studies_for_model(model_id: int):
    """
    Get studies from db that have not yet been evaluated by a given model

    Args:
        model_id (int): the db id of the model

    Returns:
        List: a list of unevaluated studies
    """

    model = model_db.get_model(model_id)

    sql = f'''
    SELECT * FROM study s
    LEFT JOIN study_evaluation se on s.id = se."studyId"
    WHERE (se.id IS NULL OR se."modelId" <> {model_id}) and se.status is null and s.type = '{model["input"]}'
    '''

    studies = query_and_fetchall(sql)

    return studies

def remove_study_by_id(orthanc_id: str):
    """
    Removes a study from the db by its orthanc ID

    Args:
        orthanc_id (str): the study id of the orthanc study
    """
    sql = f'''
    DELETE FROM study
    WHERE "orthancStudyId"='{orthanc_id}'
    '''

    query(sql)

def remove_orphan_studies():
    """
    removes studies that don't have a type
    """

    sql = '''
    DELETE FROM study
    WHERE type is NULL
    '''

    query(sql)
    print('cleaned orphan studies')

def get_studies() -> List[Dict]:
    """
    gets all db studies

    Returns
        List[Dict]: all of the studies in the database
    """

    sql = '''
    SELECT * FROM study
    '''

    return query_and_fetchall(sql)

def save_patient_id(patient_id: str, orthanc_id: str, modality: str, study_uid:str):
    """
    Saves a patient id to the database for a study

    Args:
        patient_id (str): the patient id from orthanc
        orthanc_id (str): the study id from orthanc
        modality (str): the study id from orthanc
        study_uid (str): the study uid from the dicom
    """

    sql = f'''
    UPDATE study
    SET "patientId"='{patient_id}', modality='{modality}', "studyUid"='{study_uid}'
    WHERE "orthancStudyId"='{orthanc_id}'
    '''

    query(sql)

def save_study_type(orthanc_id: str, study_type: str) -> Dict:
    """
    Saves a study to the database with it accompanying type

    Args:
        orthanc_id (str): the study ID from orthanc
        study_type (str): the type of the study (e.g. Frontal_CXR)

    Returns:
        Dict: the inserted study
    """

    sql = f'''
    UPDATE study
    SET type='{study_type}'
    WHERE "orthancStudyId"='{orthanc_id}'
    '''

    query(sql)

def insert_studies(orthanc_ids: list) -> Dict:
    """
    Saves a study to the database with it accompanying type

    Args:
        orthanc_id (int): the study ID from orthanc
        study_type (str): the type of the study (e.g. Frontal_CXR)

    Returns:
        Dict: the inserted study as dict
    """
    if len(orthanc_ids) == 0:
        return None
    orthanc_ids = map(lambda x: f'(\'{x}\')', orthanc_ids)

    sql = f'''
    INSERT INTO study ("orthancStudyId")
    VALUES {','.join(orthanc_ids)}
    RETURNING id;
    '''

    return query_and_fetchall(sql)