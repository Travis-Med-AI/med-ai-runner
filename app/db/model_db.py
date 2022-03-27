"""Database queries used by med-ai runner"""

import json
from typing import Dict, List
from db.models import EvalJob, Model
from utils.db_utils import DBConn


def get_model(model_id: int) -> Dict:
    """
    selects a single model from the database by id

    Args:
        model_id (int): the database id of the model

    Returns:
        Dict: a dictionary containing the model
    """

    # sql = f'''
    # select * from model
    # where id={model_id}
    # '''

    with DBConn() as session:
        model = session.query(Model).filter(Model.id==model_id).scalar()

    return model

def get_jobs_to_quickstart() -> List[Model]:
    """
    selects all models from database with quickstart enabled that are not currently running

    Returns:
        Dict: a dictionary containing the model
    """    
    
    # sql = '''
    # SELECT * FROM model
    # where running=false and "quickStart"=true
    # '''
    with DBConn() as session:
        jobs = session.query(EvalJob).all()

    return jobs

def stop_all_models():
    """
    sets a model as quickstarted

    Args:
        model_ids (List[int]): the models to mark as quick started
    """

    # sql = f'''
    # UPDATE model
    # SET "running"=false
    # '''

    with DBConn() as session:
        model = session.query(Model)
        model.running = False

    
def get_job_by_model(model_id: int):
    with DBConn() as session:
        job = session.query(EvalJob).filter(EvalJob.modelId==model_id).scalar()
    return job

def mark_model_as_stopped(model_id):
    """
    sets a model as quickstarted

    Args:
        model_ids (List[int]): the models to mark as quick started
    """

    # sql = f'''
    # UPDATE model
    # SET "running"=false
    # WHERE id = {model_id}
    # '''
    with DBConn() as session:
        model = session.query(Model).filter(Model.id==model_id)
