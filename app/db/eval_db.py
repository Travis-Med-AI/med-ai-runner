"""Database queries used by med-ai runner"""

import json
from typing import List, Dict

from medaimodels import ModelOutput

from utils.db_utils import query_and_fetchall, query_and_fetchone, query, join_for_in_clause
from services import logger_service, messaging_service


def add_stdout_to_eval(eval_ids: List[int], lines: List[str]):
    studies = get_study_evals(eval_ids)

    stdout = []

    if studies[0]['stdout'] is not None:
        stdout = studies[0]['stdout']

    stdout = stdout + lines
    sql = f'''
    UPDATE study_evaluation
    SET stdout=(%s)
    WHERE id in ({join_for_in_clause(eval_ids)})
    '''

    query(sql, json.dumps(stdout))

def get_study_evals(eval_ids: List[int]):
    sql = f'''
    SELECT * from study_evaluation
    WHERE id in ({join_for_in_clause(eval_ids)})
    '''

    return query_and_fetchall(sql)

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

def get_failed_eval_ids_by_exp(experimentId: int) -> List[int]:
    """
    Get ids of all failed evaluations

    Args:
        model_id (int): the db id of the model

    Returns:
        List[int]: a list of the failed evals' ids
    """

    sql = f'''
    SELECT * FROM study_evaluation se
    INNER JOIN experiment_studies_study es on es."studyId" = se."studyId"
    WHERE es."experimentId" = {experimentId} 
    '''

    evals = query_and_fetchall(sql)


    return [eval['id'] for eval in evals]

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

def update_eval_status_and_save(output: ModelOutput, eval_id: int):
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

def start_study_evaluations(studies: List[object], model_id: int) -> List[int]:
    """
    inserts entries into the study_evaluation table and sets them to 'RUNNING'

    Args:
        studies (List[object]): a list of the primary keys of study db entries to evaluate
        model (int): the id of the model to use in evalution

    Returns:
        List[int]: a list of ids of the db entries that were inserted
    """

    logger_service.log(f'starting study evaluations for {studies}')

    for study in studies:
        messaging_service.send_notification(f"Started evaluation of study {study['orthancStudyId']}", 'eval_started')
    # create string that contains the insert values for the studies
    # kind of janky TBH
    values = [f'(\'{study["id"]}\', null, \'RUNNING\', {model_id})' for study in studies]

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