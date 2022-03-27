"""Database queries used by med-ai runner"""

import json
from typing import List, Dict
from utils.db_utils import DBConn
from db.models import Classifier, EvalJob, Experiment, Model, Study, StudyEvaluation

from medaimodels import ModelOutput

from services import logger_service, messaging_service


def get_study_evals(eval_ids) -> List[StudyEvaluation]:
    with DBConn() as session:
        evals = session.query(StudyEvaluation).filter(StudyEvaluation.id.in_(eval_ids)).all()
    return evals

def add_stdout_to_eval(eval_ids: List[int], lines: List[str]):
    with DBConn() as session:
        print('evalids are ', eval_ids)
        studies = get_study_evals(eval_ids)

        stdout = []

        if studies[0].stdout is not None:
            stdout = studies[0].stdout

        stdout = stdout + lines
        evaluations = session.query(StudyEvaluation).\
                    filter(StudyEvaluation.id.in_(eval_ids)).all()
        for e in evaluations:
            e.stdout = stdout


def get_default_model():
    """
    Gets the default classifier model

    Returns:
        Dict: the default classifier model
    """
    with DBConn() as session:
        model = session.query(Classifier).join(Model).scalar()
    return model

def remove_orphan_evals():
    """
    removes evaluations that don't have an output
    """
    with DBConn() as session:

        session.query(StudyEvaluation).filter(StudyEvaluation.modelOutput == None).\
                                        delete()
    print('cleaned orphan evals')

def get_failed_eval_ids(model_id: int) -> List[int]:
    """
    Get ids of all failed evaluations

    Args:
        model_id (int): the db id of the model

    Returns:
        List[int]: a list of the failed evals' ids
    """

    with DBConn() as session:

        evals: List[StudyEvaluation] = session.query(StudyEvaluation).\
                                                filter(StudyEvaluation.status == 'FAILED').\
                                                filter(StudyEvaluation.modelId == model_id).\
                                                all()
    return [e.id for e in evals]

def get_failed_eval_ids_by_exp(experimentId: int) -> List[int]:
    """
    Get ids of all failed evaluations

    Args:
        model_id (int): the db id of the model

    Returns:
        List[int]: a list of the failed evals' ids
    """

    # sql = f'''
    # SELECT * FROM study_evaluation se
    # INNER JOIN experiment_studies_study es on es."studyId" = se."studyId"
    # WHERE es."experimentId" = {experimentId} and se."status"='FAILED'
    # '''

    with DBConn() as session:

        evals: List[StudyEvaluation] = session.query(StudyEvaluation).\
                                                join(Study).\
                                                filter(Experiment.study.any(id=Study.id)).\
                                                filter(StudyEvaluation.status == 'FAILED').\
                                                filter(Experiment.id == experimentId).\
                                                all()
    return [e.id for e in evals]

def fail_eval(eval_id: int):
    """
    Updates study evalutation status to failed

    Args:
        eval_id (int): the db id of the study evaluation
    """

    # sql = f'''
    # UPDATE study_evaluation 
    # SET status='FAILED'
    # WHERE id={eval_id}
    # '''
    with DBConn() as session:

        evaulation = session.query(StudyEvaluation).filter(StudyEvaluation.id == eval_id).\
                                            scalar()
        evaulation.status = 'FAILED'
    return evaulation

def get_eval_jobs() -> List[Dict]:
    """
    Selects all eval jobs that are currently set to running and are not expired

    Returns:
        List: all current eval jobs ordered by last run
    """

    # # selects all eval jobs that are currently set to running
    # sql = '''
    # SELECT * FROM eval_job ej
    # WHERE "running"=true
    # ORDER BY "lastRun"
    # '''

    with DBConn() as session:

        eval_jobs = session.query(EvalJob).filter(EvalJob.running==True).\
                                        order_by(EvalJob.lastRun).all()
    return eval_jobs

def update_eval_status_and_save(output: ModelOutput, eval_id: int) -> StudyEvaluation:
    """
    Updates study evalutation status to completed and saves the model output

    Args:
        output (ModelOutput): the output of the model
        eval_id (int): the id of the eval to be update
    """
    ### set eval as completed and save model output as json
    # sql = f'''
    # UPDATE study_evaluation 
    # SET status='COMPLETED', "modelOutput"=('{json.dumps(output)}') {update_sql_string}
    # WHERE id={eval_id}
    # '''
    with DBConn() as session:

        evaluation = session.query(StudyEvaluation).filter(StudyEvaluation.id == eval_id).\
                                            scalar()
        evaluation.status = 'COMPLETED'
        evaluation.modelOutput = output
        evaluation.imgOutputPath = output['image'] if output and output['image'] else None
    return evaluation

def restart_failed_evals(eval_ids: List[int]):
    """
    sets a failed evaluation to status 'RUNNING' to restart it

    Args:
        eval_ids (List[int]): a list of the ids of evals to be restarted
    """

    with DBConn() as session:
        if len(eval_ids) == 0:
            return

        # sql = f'''
        # UPDATE study_evaluation
        # SET status='RUNNING'
        # WHERE id in ({ids})
        # '''
        evaluation = session.query(StudyEvaluation).filter(StudyEvaluation.id.in_(eval_ids)).scalar()

        evaluation.status = 'RUNNING'


def start_study_evaluations(studies: List[Study], model_id: int) -> List[int]:
    """
    inserts entries into the study_evaluation table and sets them to 'RUNNING'

    Args:
        studies (List[object]): a list of the primary keys of study db entries to evaluate
        model (int): the id of the model to use in evalution

    Returns:
        List[int]: a list of ids of the db entries that were inserted
    """

    with DBConn() as session:             
        logger_service.log(f'starting study evaluations for {studies}')

        for study in studies:
            messaging_service.send_notification(f"Started evaluation of study {study.orthancStudyId}", 'eval_started', -1)

        if len(studies) == 0:
            return []

        # # query and fetch all results
        # sql = f'''
        # INSERT INTO study_evaluation ("studyId", "modelOutput", status, "modelId")
        # VALUES {reduced}
        # RETURNING id;
        # '''
        model:Model = session.query(Model).filter(Model.id==model_id).scalar()
        evals_to_add = [StudyEvaluation(studyId=study.id,
                                        modelOutput=None,
                                        status='RUNNING',
                                        modelId=model_id,
                                        userId=model.userId) for study in studies]
        session.add_all(evals_to_add)
        study_ids = [study.id for study in studies]
        evals: List[StudyEvaluation] = session.query(StudyEvaluation).\
                                                    filter(StudyEvaluation.studyId.in_(study_ids)).\
                                                    all()

    return [e.id for e in evals]