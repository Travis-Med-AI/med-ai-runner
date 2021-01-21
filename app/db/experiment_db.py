"""Database queries used by med-ai runner"""

import json
from typing import List, Dict

from medaimodels import ModelOutput

from utils.db_utils import query_and_fetchall, query_and_fetchone, query, join_for_in_clause


def get_studies_for_experiment(experiment_id):
    """
    """
    sql = f'''
    SELECT  distinct s.* FROM study s
    LEFT JOIN study_evaluation se on s.id = se."studyId"
    INNER JOIN experiment_studies_study es on s.id = es."studyId"
    WHERE se.id is null
    '''

    studies = query_and_fetchall(sql)

    return studies


def get_running_experiments():
    """
    """
    sql = f'''
    SELECT * FROM experiment e
    WHERE e.status = 'RUNNING'
    '''

    experiments = query_and_fetchall(sql)

    return experiments

def set_experiment_complete(experiment_id):
    """
    """
    sql = f'''
    UPDATE experiment
    SET "status"='COMPLETED'
    WHERE id='{experiment_id}'
    '''

    query(sql)

def set_experiment_failed(experiment_id):
    """
    """
    sql = f'''
    UPDATE experiment
    SET "status"='STOPPED'
    WHERE id='{experiment_id}'
    '''

    query(sql)