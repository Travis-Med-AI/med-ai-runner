import time

import atexit
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine 
import os
import pika

db_connection = None
rabbit_connection = None
rabbit_channel = None

def init_db():
    """
    Initializes the database connection pool required by the application to connect to the database.
    """
    global db_connection
    if db_connection is None:
        print('initializing db connection')
        engine = create_engine('postgresql://test:test@postgres-db:5432/ai', isolation_level="READ UNCOMMITTED")
        import db.models as models
        Session = sessionmaker(bind=engine)
        db_connection = Session()
    else:
        print("The connection pool has already been initialized.")

def init_rabbit():
    global rabbit_channel
    global rabbit_connection
    global rabbit_channel

    print('opening db connection')
    rabbit_url = os.getenv('RABBIT_MQ_URL') or 'amqp://guest:guest@rabbitmq:5672'
    rabbit_connection = pika.BlockingConnection(pika.URLParameters(rabbit_url))
    rabbit_channel = rabbit_connection.channel()

class DBConn:
    """
    To connect to the database, it is preferred to use the pattern:
    with DBConn() as conn:
        ...
    It will ensure that the connection is taken from the connection pool return it to the pool
    when done. The pool must be initialized first via `init_db_pool()`.
    """

    def __init__(self):
        if db_connection is None:
            raise ValueError("The database connection pool has not been initialized by the application."
                             " Use 'init_db_pool()' to initialise it.")
        self.session = db_connection

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, traceback):
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise


class RabbitConn:
    """
    To connect to the database, it is preferred to use the pattern:
    with DBConn() as conn:
        ...
    It will ensure that the connection is taken from the connection pool return it to the pool
    when done. The pool must be initialized first via `init_db_pool()`.
    """

    def __init__(self):
        if rabbit_channel is None:
            raise ValueError("The rabbit connection has not been initialized by the application."
                             " Use 'init_rabbit()' to initialise it.")
        self.channel = rabbit_channel

    def __enter__(self):
        print('entering rabbit connection')
        if self.channel:
            init_rabbit()
            self.channel = rabbit_channel
        return self.channel
    
    def __exit__(self, exc_type, exc_val, traceback):
        print('exiting rabbit connection')

@atexit.register
def close_rabbit():
    global rabbit_connection
    if rabbit_connection:
        rabbit_connection.close()

@atexit.register
def close_db_pool():
    """
    If a connection pool is available, close all its connections and set it to None.
    This method is always run at the exit of the application, to ensure that we free as much as possible
    the database connections.
    """
    global db_connection
    if db_connection is not None:
        db_connection.rollback()
        db_connection.close()
        db_connection = None
