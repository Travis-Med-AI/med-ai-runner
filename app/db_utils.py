"""db utils that are used by all queries"""

import traceback
from typing import Dict, List

from psycopg2 import connect
from psycopg2.extras import DictCursor
import logger


def get_pg_connection() -> (Dict, Dict):
    """
    Gets pg connection and cursor from postgres

    Returns:
        (Dict, Dict): the pg connection and cursor
    """
    try:
        pg_conn = connect(host='postgres-db', user='test', password='test', dbname='ai')
        pg_cur = pg_conn.cursor(cursor_factory=DictCursor)

        return pg_conn, pg_cur
    except Exception as e:
        traceback.print_exc()
        logger.log_error('DB ERROR', traceback.format_exc())
        raise e


def query_and_fetchone(sql_query: str) -> Dict:
    """
    takes a sql query string and returns the first row of the results of the query

    Args:
        sql_query: the SQL query

    Returns:
        Dict: A single row from the query
    """
    try:
        pg_conn, pg_cur = get_pg_connection()

        pg_cur.execute(sql_query)

        result = pg_cur.fetchone()

        pg_conn.commit()
        pg_cur.close()
        pg_conn.close()

        return result

    except Exception as e:
        traceback.print_exc()
        logger.log_error('DB ERROR', traceback.format_exc())
        raise e


def query_and_fetchall(sql_query: str) -> List[Dict]:
    """
    takes a sql query string and returns the all rows of the results of the query

    Args:
        sql_query: the SQL query

    Returns:
        List[Dict]: All rows from the query
    """
    try:
        pg_conn, pg_cur = get_pg_connection()

        pg_cur.execute(sql_query)

        result = pg_cur.fetchall()

        pg_conn.commit()
        pg_cur.close()
        pg_conn.close()

        return result
    except Exception as e:
        traceback.print_exc()
        logger.log_error('DB ERROR', traceback.format_exc())
        raise e


def query(sql_query: str):
    """
    takes a sql query string and returns the all rows of the results of the query

    Args:
        sql_query: the SQL query
    """

    try:
        pg_conn, pg_cur = get_pg_connection()

        pg_cur.execute(sql_query)

        pg_conn.commit()
        pg_cur.close()
        pg_conn.close()
    except Exception as e:
        traceback.print_exc()
        logger.log_error('DB ERROR', traceback.format_exc())
        raise e
