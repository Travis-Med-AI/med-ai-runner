"""Database queries used by med-ai runner"""

import json
from typing import List, Dict

from medaimodels import ModelOutput

from utils.db_utils import query_and_fetchall, query_and_fetchone, query, join_for_in_clause

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