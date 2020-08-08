"""db utils that are used by all queries"""

from typing import Dict, List

from psycopg2 import connect
from psycopg2.extras import DictCursor


def get_pg_connection() -> (Dict, Dict):
    """
    Gets pg connection and cursor from postgres

    Returns:
        (Dict, Dict): the pg connection and cursor
    """
    pg_conn = connect(host='postgres-db', user='test', password='test', dbname='ai')
    pg_cur = pg_conn.cursor(cursor_factory=DictCursor)

    return pg_conn, pg_cur


def query_and_fetchone(sql_query: str) -> Dict:
    """
    takes a sql query string and returns the first row of the results of the query

    Args:
        sql_query: the SQL query

    Returns:
        Dict: A single row from the query
    """
    pg_conn, pg_cur = get_pg_connection()

    pg_cur.execute(sql_query)

    result = pg_cur.fetchone()

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()

    return result


def query_and_fetchall(sql_query: str) -> List[Dict]:
    """
    takes a sql query string and returns the all rows of the results of the query

    Args:
        sql_query: the SQL query

    Returns:
        List[Dict]: All rows from the query
    """
    pg_conn, pg_cur = get_pg_connection()

    pg_cur.execute(sql_query)

    result = pg_cur.fetchall()

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()

    return result


def query(sql_query: str):
    """
    takes a sql query string and returns the all rows of the results of the query

    Args:
        sql_query: the SQL query
    """
    pg_conn, pg_cur = get_pg_connection()

    pg_cur.execute(sql_query)

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()
