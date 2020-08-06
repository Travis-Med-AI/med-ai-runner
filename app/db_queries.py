from db_utils import query_and_fetchall, query_and_fetchone, query
import json
import time
import numpy as np
from medaimodels import ModelOutput

def start_study_evaluations(studies: list, modelId: int):
    """
    inserts entries into the study_evaluation table and sets them to 'RUNNING'

    :param studyIds: a list of the primary keys of study db entries to evaluate
    :param modelId: the id of the model to use in evalution

    :return: a list of all db entries that were inserted
    """
    values = [f'(\'{study[0]}\', null, \'RUNNING\', {modelId})' for study in studies]

    if len(studies) == 0:
        return []

    reduced = ','.join(list(values))

    sql = f'''
    INSERT INTO study_evaluation ("studyId", "modelOutput", status, "modelId")
    VALUES {reduced}
    RETURNING id;
    '''

    query_result = query_and_fetchall(sql)

    study_eval = map(lambda x: x['id'], query_result)

    return list(study_eval)


def restart_failed_evals(eval_ids:list, modelId:int):
    if len(eval_ids) == 0:
        return


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
    
    :param output: the output of the model
    :param eval_id: the db id of the study evaluation

    :return: the updated study evaluation

    """

    update_sql_string = ''
    if output['image']:
        img_path = output['image']
        update_sql_string = f', "imgOutputPath"=\'{img_path}\''

    sql = f'''
    UPDATE study_evaluation 
    SET status='COMPLETED', "modelOutput"=('{json.dumps(output)}') {update_sql_string}
    WHERE id={eval_id}
    '''

    query(sql)


def get_eval_jobs():
    """
    Selects all eval jobs that are currently set to running and are not expired

    :return: all current eval jobs ordred by last run
    """
    sql = f'''
    SELECT * FROM eval_job ej
    WHERE "running"=true
    ORDER BY "lastRun"
    '''

    study_evals = query_and_fetchall(sql)

    return study_evals


def fail_eval(eval_id):
    """
    Updates study evalutation status to failed

    :param eval_id: the db id of the study evaluation

    :return: the updated study evaluation
    """

    sql = f'''
    UPDATE study_evaluation 
    SET status='FAILED'
    WHERE id={eval_id}
    '''

    query(sql)


def get_model(model_id):
    """
    selects a single model from the database by id
    
    :param model_id: the database id of the model

    :return: a dict containing the model 
    """
    sql = f'''
    select * from model
    where id={model_id}
    '''

    model = query_and_fetchone(sql)

    return model



def insert_studies(orthanc_ids: list):
    """
    Saves a study to the database with it accompanying type

    :param orthanc_id: the study id from orthanc
    :param study_type: the type of the study (e.g. AP_CXR)

    :return: the inserted study as dict
    """
    if len(orthanc_ids) == 0:
        return
    orthanc_ids = map(lambda x: f'(\'{x}\')', orthanc_ids)

    sql = f'''
    INSERT INTO study ("orthancStudyId")
    VALUES {','.join(orthanc_ids)}
    RETURNING id;
    '''

    study = query_and_fetchall(sql)

    return study


def save_study_type(orthanc_id: str, study_type: str):
    """
    Saves a study to the database with it accompanying type

    :param orthanc_id: the study id from orthanc
    :param study_type: the type of the study (e.g. AP_CXR)

    :return: the inserted study as dict
    """

    sql = f'''
    UPDATE study
    SET type='{study_type}'
    WHERE "orthancStudyId"='{orthanc_id}'
    '''

    query(sql)


def save_patient_id(patient_id, orthanc_id, modality):
    """
    Saves a patient id to the database for study

    :param patient_id: the patient id from orthanc
    :param orthanc_id: the study id from orthanc
    """

    sql = f'''
    UPDATE study
    SET "patientId"='{patient_id}', modality='{modality}'
    WHERE "orthancStudyId"='{orthanc_id}'
    '''

    query(sql)

def get_studies_for_model(model_id):
    """
    Get studies from db that have not yet been evaluated by a given model

    :param model_id: the db id of the model

    :returns: a list of unevaluated studies
    """

    model = get_model(model_id)

    sql = f'''
    SELECT * FROM study s
    LEFT JOIN study_evaluation se on s.id = se."studyId"
    WHERE (se.id IS NULL OR se."modelId" <> {model_id}) 
          AND s.type = '{model['input']}'
    '''

    studies = query_and_fetchall(sql)

    return studies


def get_failed_eval_ids(model_id):

    sql = f'''
    SELECT * FROM study_evaluation se
    WHERE se."status" = 'FAILED' and se."modelId"={model_id}
    '''

    evals = query_and_fetchall(sql)


    return [eval['id'] for eval in evals]


def get_classifier_model():
    """
    Gets classifier model from the database
    """

    sql = f'''
    SELECT * FROM classifier c
    '''

    classifier = query_and_fetchone(sql)

    return classifier['modelId']

def get_studies():
    """
    gets all db studies
    """

    sql = f'''
    SELECT * FROM study
    '''

    return query_and_fetchall(sql)

def fail_classifer(study_id):
    """
    Updates study evalutation status to failed

    :param eval_id: the db id of the study evaluation

    :return: the updated study evaluation
    """

    sql = f'''
    UPDATE study 
    SET failed=true
    WHERE "orthancStudyId"='{study_id}'
    '''

    query(sql)

def remove_orphan_studies():
    sql = f'''
    DELETE FROM study
    WHERE type is NULL
    '''

    query(sql)
    print('cleaned orphan studies')

def remove_study_by_id(orthanc_id):
    sql = f'''
    DELETE FROM study
    WHERE "orthancStudyId"='{orthanc_id}'
    '''

    query(sql)

def remove_orphan_evals():
    sql = f'''
    DELETE FROM study_evaluation
    WHERE "modelOutput" is NULL
    '''

    query(sql)
    print('cleaned orphan evals')

def get_classifier_model(modality):
    sql = f'''
    SELECT m.* FROM classifier c 
    JOIN model m ON c."modelId"=m.id
    WHERE m.modality = '{modality}'
    '''

    return query_and_fetchone(sql)
    
def get_default_model():
    sql = f'''
    SELECT m.* FROM classifier c 
    JOIN model m ON c."modelId"=m.id
    '''
    return query_and_fetchone(sql)