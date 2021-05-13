"""Database queries used by med-ai runner"""

import json
from typing import List, Dict

from medaimodels import ModelOutput

from utils.db_utils import query_and_fetchall, query_and_fetchone, query, join_for_in_clause


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

def get_models_to_quickstart():
    """
    selects all models from database with quickstart enabled that are not currently running

    Returns:
        Dict: a dictionary containing the model
    """    
    
    sql = '''
    SELECT * FROM model
    where running=false and "quickStart"=true
    '''

    return query_and_fetchall(sql)

def mark_models_as_quickstarted(model_ids):
    """
    sets a model as quickstarted

    Args:
        model_ids (List[int]): the models to mark as quick started
    """

    sql = f'''
    UPDATE model
    SET "running"=true
    WHERE "id" in ({join_for_in_clause(model_ids)})
    '''

    query(sql)

def stop_all_models():
    """
    sets a model as quickstarted

    Args:
        model_ids (List[int]): the models to mark as quick started
    """

    sql = f'''
    UPDATE model
    SET "running"=false
    '''

    query(sql)

def mark_model_as_stopped(model_id):
    """
    sets a model as quickstarted

    Args:
        model_ids (List[int]): the models to mark as quick started
    """

    sql = f'''
    UPDATE model
    SET "running"=false
    WHERE id = {model_id}
    '''

    query(sql)