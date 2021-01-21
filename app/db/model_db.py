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