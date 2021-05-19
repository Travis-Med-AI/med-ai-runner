"""Database queries used by med-ai runner"""

import json
from typing import List, Dict


from utils.db_utils import query_and_fetchall, query_and_fetchone, query, join_for_in_clause

def get_settings() -> Dict:
    sql = f'''
    select * from app_settings
    '''

    model = query_and_fetchone(sql)

    return model