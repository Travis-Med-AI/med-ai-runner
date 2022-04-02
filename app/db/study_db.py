"""Database queries used by med-ai runner"""

import json
from typing import List, Dict
from utils.db_utils import DBConn
from services.orthanc_service import OrthancMetadata
from sqlalchemy import or_, and_

from services import logger_service
from db.models import Model, Study, StudyEvaluation

def get_study_by_orthanc_id(orthanc_id: str) -> Study:
    """
    Gets a study by orthanc_id
    Args:
        orthanc_id (str): the orthanc_study
    Returns:
        Dict: the default classifier model
    """
    with DBConn() as session:
        logger_service.log(f'inserting study for orthanc Id: {orthanc_id}')
        study: List[Study] = session.query(Study).filter(Study.orthancStudyId==orthanc_id).scalar()
    return study

def get_studies_for_model(model_id: int) ->List[Study]:
    """
    Get studies from db that have not yet been evaluated by a given model

    Args:
        model_id (int): the db id of the model

    Returns:
        List: a list of unevaluated studies
    """
    with DBConn() as session:
        model:Model = session.query(Model).filter(Model.id==model_id).scalar()
        print(model.id)
        studies: List[Study] = session.query(Study).\
                                            join(StudyEvaluation, and_(StudyEvaluation.studyId == Study.id, StudyEvaluation.modelId == model.id), isouter=True).\
                                            filter(Study.modality == model.modality).\
                                            filter(StudyEvaluation.id == None)

        studies = studies.all()


    return studies

def remove_study_by_id(orthanc_id: str):
    """
    Removes a study from the db by its orthanc ID

    Args:
        orthanc_id (str): the study id of the orthanc study
    """
    with DBConn() as session:
        session.query(Study).filter(Study.orthancStudyId == orthanc_id).delete()


def remove_orphan_studies():
    """
    removes studies that don't have a type
    """
    with DBConn() as session:
        session.query(Study).filter(Study.type == None).delete()


    print('cleaned orphan studies')

def get_studies() -> List[Study]:
    """
    gets all db studies

    Returns
        List[Dict]: all of the studies in the database
    """

    with DBConn() as session:
        studies = session.query(Study).all()

    return studies

def save_patient_metadata(metadata: OrthancMetadata):
    """
    Saves a patient id to the database for a study

    Args:
        metadata (OrthancMetadata): metdata from orthanc
    """

    with DBConn() as session:
        study = session.query(Study).filter(Study.orthancStudyId == metadata.orthanc_id).scalar()
        study.patientId = metadata.patient_id, 
        study.modality = metadata.modality, 
        study.studyUid = metadata.study_uid, 
        study.seriesUid = metadata.series_uid, 
        study.accession = metadata.accession,
        study.description = metadata.description
        study.seriesMetadata = json.dumps(metadata.series_metadta)
        study.studyMetadata = json.dumps(metadata.study_metadta)


                            

def save_study_type(orthanc_id: str, study_type: str) -> Dict:
    """
    Saves a study to the database with it accompanying type

    Args:
        orthanc_id (str): the study ID from orthanc
        study_type (str): the type of the study (e.g. Frontal_CXR)

    Returns:
        Dict: the inserted study
    """
    with DBConn() as session:

        study = session.query(Study).filter(Study.orthancStudyId==orthanc_id).scalar()
        study.type = study_type
    return study



def insert_studies(orthanc_ids: list) -> Dict:
    """
    Saves a study to the database with it accompanying type

    Args:
        orthanc_id (int): the study ID from orthanc
        study_type (str): the type of the study (e.g. Frontal_CXR)

    Returns:
        Dict: the inserted study as dict
    """
    with DBConn() as session:
        if len(orthanc_ids) == 0:
            return None
        studies = [Study(orthancStudyId = orthanc_id) for orthanc_id in orthanc_ids]

        session.add_all(studies)
        studies = session.query(Study).\
                            filter(Study.orthancStudyId.in_(orthanc_ids)).\
                            all()


    return studies

def get_study_by_eval_id(eval_id):
    with DBConn() as session:
        study = session.query(Study, StudyEvaluation).\
                    filter(Study.id == StudyEvaluation.studyId).\
                    filter(StudyEvaluation.id==eval_id).scalar()

    return study