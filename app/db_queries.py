"""Database queries used by med-ai runner"""

import json
from typing import List, Dict

from medaimodels import ModelOutput

import logger 
import messaging
from db_utils import query_and_fetchall, query_and_fetchone, query, join_for_in_clause

def start_study_evaluations(studies: List[object], model_id: int) -> List[int]:
    """
    inserts entries into the study_evaluation table and sets them to 'RUNNING'

    Args:
        studies (List[object]): a list of the primary keys of study db entries to evaluate
        model (int): the id of the model to use in evalution

    Returns:
        List[int]: a list of ids of the db entries that were inserted
    """

    logger.log(f'starting study evaluations for {studies}')

    for study in studies:
        messaging.send_notification(f"Started evaluation of study {study['orthancStudyId']}", 'eval_started')
    # create string that contains the insert values for the studies
    # kind of janky TBH
    values = [f'(\'{study[0]}\', null, \'RUNNING\', {model_id})' for study in studies]

    if len(studies) == 0:
        return []

    # join the insert arrays by , so that it can be used to insert multiple
    reduced = ','.join(list(values))

    # query and fetch all results
    sql = f'''
    INSERT INTO study_evaluation ("studyId", "modelOutput", status, "modelId")
    VALUES {reduced}
    RETURNING id;
    '''
    query_result = query_and_fetchall(sql)

    return [evaluation['id'] for evaluation in query_result]


def restart_failed_evals(eval_ids: List[int]):
    """
    sets a failed evaluation to status 'RUNNING' to restart it

    Args:
        eval_ids (List[int]): a list of the ids of evals to be restarted
    """

    if len(eval_ids) == 0:
        return

    # join ids by , so that it can be used in WHERE ... IN clause
    ids = ','.join([str(eval_id) for eval_id in eval_ids])

    sql = f'''
    UPDATE study_evaluation
    SET status='RUNNING'
    WHERE id in ({ids})
    '''

    query(sql)


def update_db(output: ModelOutput, eval_id: int):
    """
    Updates study evalutation status to completed and saves the model output

    Args:
        output (ModelOutput): the output of the model
        eval_id (int): the id of the eval to be update
    """

    # checks output to see if it output an image and adds imgOutputPath to SQL string
    update_sql_string = ''
    if output['image']:
        img_path = output['image']
        update_sql_string = f', "imgOutputPath"=\'{img_path}\''

    ### set eval as completed and save model output as json
    sql = f'''
    UPDATE study_evaluation 
    SET status='COMPLETED', "modelOutput"=('{json.dumps(output)}') {update_sql_string}
    WHERE id={eval_id}
    '''

    query(sql)


def get_eval_jobs() -> List[Dict]:
    """
    Selects all eval jobs that are currently set to running and are not expired

    Returns:
        List: all current eval jobs ordered by last run
    """

    # selects all eval jobs that are currently set to running
    sql = '''
    SELECT * FROM eval_job ej
    WHERE "running"=true
    ORDER BY "lastRun"
    '''

    study_evals = query_and_fetchall(sql)

    return study_evals


def fail_eval(eval_id: int):
    """
    Updates study evalutation status to failed

    Args:
        eval_id (int): the db id of the study evaluation
    """

    sql = f'''
    UPDATE study_evaluation 
    SET status='FAILED'
    WHERE id={eval_id}
    '''

    query(sql)


def get_model(model_id: int) -> Dict:
    """
    selects a single model from the database by id

    Args:
        model_id (int): the database id of the model

    Returns:
        Dict: a dictionary containing the model
    """

    sql = f'''
    select * from model
    where id={model_id}
    '''

    model = query_and_fetchone(sql)

    return model


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

def get_studies_for_model(model_id: int):
    """
    Get studies from db that have not yet been evaluated by a given model

    Args:
        model_id (int): the db id of the model

    Returns:
        List: a list of unevaluated studies
    """

    model = get_model(model_id)

    sql = f'''
    SELECT * FROM study s
    LEFT JOIN study_evaluation se on s.id = se."studyId"
    WHERE (se.id IS NULL OR se."modelId" <> {model_id}) and se.status is null and s.type = '{model["input"]}'
    '''

    studies = query_and_fetchall(sql)

    return studies


def get_failed_eval_ids(model_id: int) -> List[int]:
    """
    Get ids of all failed evaluations

    Args:
        model_id (int): the db id of the model

    Returns:
        List[int]: a list of the failed evals' ids
    """

    sql = f'''
    SELECT * FROM study_evaluation se
    WHERE se."status" = 'FAILED' and se."modelId"={model_id}
    '''

    evals = query_and_fetchall(sql)


    return [eval['id'] for eval in evals]


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

def fail_classifer(study_id: int):
    """
    Updates study evalutation status to failed

    Args:
        eval_id: the db id of the failed evaluation
    """

    sql = f'''
    UPDATE study 
    SET failed=true
    WHERE "orthancStudyId"='{study_id}'
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


def remove_orphan_evals():
    """
    removes evaluations that don't have an output
    """
    sql = '''
    DELETE FROM study_evaluation
    WHERE "modelOutput" is NULL
    '''

    query(sql)
    print('cleaned orphan evals')


def get_classifier_model(modality: str):
    """
    Gets a classifier model for a given modality

    Args:
        modality (str): the modality of the studies

    Returns:
        Dict: the classifer model that pertains to the given modality
    """

    sql = f'''
    SELECT m.* FROM classifier c 
    JOIN model m ON c."modelId"=m.id
    WHERE m.modality = '{modality}'
    '''

    return query_and_fetchone(sql)


def get_default_model():
    """
    Gets the default classifier model

    Returns:
        Dict: the default classifier model
    """
    sql = '''
    SELECT m.* FROM classifier c 
    JOIN model m ON c."modelId"=m.id
    '''
    return query_and_fetchone(sql)

def get_study_by_orthanc_id(orthanc_id: str):
    """
    Gets a study by orthanc_id
    Args:
        orthanc_id (str): the orthanc_study
    Returns:
        Dict: the default classifier model
    """
    logger.log(f'inserting study for orthanc Id: {orthanc_id}')
    sql = f'''
    SELECT * from study
    WHERE "orthancStudyId"='{orthanc_id}'
    '''

    return query_and_fetchone(sql)

def get_study_evals(eval_ids: List[int]):
    sql = f'''
    SELECT * from study_evaluation
    WHERE id in ({join_for_in_clause(eval_ids)})
    '''

    return query_and_fetchall(sql)


def add_stdout_to_eval(eval_ids: List[int], line: str):
    studies = get_study_evals(eval_ids)

    stdout = []

    if studies[0]['stdout'] is not None:
        stdout = studies[0]['stdout']

    stdout.append(line)
    sql = f'''
    UPDATE study_evaluation
    SET stdout=('{json.dumps(stdout)}')
    WHERE id in ({join_for_in_clause(eval_ids)})
    '''

    query(sql)