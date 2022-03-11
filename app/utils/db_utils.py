"""db utils that are used by all queries"""

import traceback
from typing import Dict, List, Tuple
from urllib.parse import urlparse
import os

from psycopg2 import connect
from psycopg2.extras import DictCursor
from services import logger_service


def get_pg_connection() -> Tuple[Dict, Dict]:
    """
    Gets pg connection and cursor from postgres

    Returns:
        (Dict, Dict): the pg connection and cursor
    """
    try:
        postgres_url = os.getenv('POSTGRES_URL') 
        if(postgres_url):

            result = urlparse.urlparse(postgres_url)
            username = result.username
            password = result.password
            database = result.path[1:]
            hostname = result.hostname
            port = result.port
            pg_conn = psycopg2.connect(
                database = database,
                user = username,
                password = password,
                host = hostname,
                port = port
            )
        else:
            pg_conn = connect(host='postgres-db', user='test', password='test', dbname='ai')
        pg_cur = pg_conn.cursor(cursor_factory=DictCursor)

        return pg_conn, pg_cur
    except Exception as e:
        traceback.print_exc()
        logger_service.log_error('DB ERROR', traceback.format_exc())
        raise e


def query_and_fetchone(sql_query: str, *args) -> Dict:
    """
    takes a sql query string and returns the first row of the results of the query

    Args:
        sql_query: the SQL query

    Returns:
        Dict: A single row from the query
    """
    try:
        pg_conn, pg_cur = get_pg_connection()

        pg_cur.execute(sql_query, args)

        result = pg_cur.fetchscalar()

        pg_conn.commit()
        pg_cur.close()
        pg_conn.close()

        return result

    except Exception as e:
        traceback.print_exc()
        logger_service.log_error('DB ERROR', traceback.format_exc())
        raise e


def query_and_fetchall(sql_query: str, *args) -> List[Dict]:
    """
    takes a sql query string and returns the all rows of the results of the query

    Args:
        sql_query: the SQL query

    Returns:
        List[Dict]: All rows from the query
    """
    try:
        pg_conn, pg_cur = get_pg_connection()

        pg_cur.execute(sql_query, args)

        result = pg_cur.fetchall()

        pg_conn.commit()
        pg_cur.close()
        pg_conn.close()

        return result
    except Exception as e:
        traceback.print_exc()
        logger_service.log_error('DB ERROR', traceback.format_exc())
        raise e


def query(sql_query: str, *args):
    """
    takes a sql query string and returns the all rows of the results of the query

    Args:
        sql_query: the SQL query
    """

    try:
        pg_conn, pg_cur = get_pg_connection()

        pg_cur.execute(sql_query, args)

        pg_conn.commit()
        pg_cur.close()
        pg_conn.close()
    except Exception as e:
        traceback.print_exc()
        logger_service.log_error('DB ERROR', traceback.format_exc())
        raise e


def join_for_in_clause(lst: List):
    if len(lst) < 1:
        return '-1'
    return ','.join([str(item) for item in lst])
