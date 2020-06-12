from psycopg2 import connect
from psycopg2.extras import DictCursor


def get_pg_connection():
    """
    Gets pg connection and cursor from postgres
    """
    pg_conn = connect(host='postgres-db', user='test', password='test', dbname='ai')
    pg_cur = pg_conn.cursor(cursor_factory=DictCursor)

    return pg_conn, pg_cur


def query_and_fetchone(sql_query: str):
    """
    takes a sql query string and returns the first row of the results of the query

    :param sql_query: the sql query
    :return: the first row of the result from the query as a dict
    """
    pg_conn, pg_cur = get_pg_connection()

    pg_cur.execute(sql_query)

    result = pg_cur.fetchone()

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()

    return result


def query_and_fetchall(sql_query: str):
    """
    takes a sql query string and returns the all rows of the results of the query

    :param sql_query: the sql query
    :return: a list containing the results of the query as a dict
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

    :param sql_query: the sql query
    :return: a list containing the results of the query as a dict
    """
    pg_conn, pg_cur = get_pg_connection()

    pg_cur.execute(sql_query)

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()
