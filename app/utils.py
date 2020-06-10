import os
from celery import Celery, shared_task
import settings
import docker
import redis
import numpy as np
import struct
from psycopg2 import connect
from psycopg2.extras import DictCursor
import time
from functools import reduce


# import postgres_settings
import json
import requests
from zipfile import ZipFile

def get_model(model_id):
    pg_conn, pg_cur = get_pg_connection()

    sql = f'''
    select * from model
    where id={model_id}
    '''

    pg_cur.execute(sql)

    model = pg_cur.fetchone()

    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()

    return model


def get_pg_connection():
    pg_conn = connect(host='postgres-db', user='test', password='test', dbname='ai')
    pg_cur = pg_conn.cursor(cursor_factory=DictCursor)

    return pg_conn, pg_cur


def fromRedis(r,n):
   """Retrieve Numpy array from Redis key 'n'"""
   encoded = r.get(n)
   h, w = struct.unpack('>II',encoded[:8])
   a = np.frombuffer(encoded, dtype=np.float, offset=8).reshape(h,w)

   return a


def get_study(study_id):
    url = f'http://orthanc:8042/studies/{study_id}/media'
    study = requests.get(url)
    out_path = f'/tmp/{study_id}'
    file_path = f'{out_path}.zip'

    open(file_path, 'wb').write(study.content)
    with ZipFile(file_path, 'r') as zipObj:
        zipObj.extractall(out_path)
    
    return study_id


def start_study_evaluations(studyIds, modelId):
    pg_conn, pg_cur = get_pg_connection()
    values = map(lambda x: f'(\'{x}\', null, \'RUNNING\', {modelId})',studyIds)
    reduced = ','.join(list(values))

    sql = f'''
    INSERT INTO study_evaluation (patient, "modelOutput", status, "modelId")
    VALUES {reduced}
    RETURNING id;
    '''

    pg_cur.execute(sql)

    study_eval = map(lambda x: x['id'], pg_cur.fetchall())
    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()

    return list(study_eval)


def get_study_ids(model_id):
    pg_conn, pg_cur = get_pg_connection()

    sql = f'''
    SELECT patient FROM study_evaluation
    WHERE "modelId"={model_id}
    '''
    pg_cur.execute(sql)

    study_eval = pg_cur.fetchall()
    print(study_eval)
    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()

    return map(lambda x: x['patient'], study_eval)


def update_db(output, id):
    pg_conn, pg_cur = get_pg_connection()

    sql = f'''
    UPDATE study_evaluation 
    SET status='COMPLETED', "modelOutput"=('{json.dumps(output.tolist())}')
    WHERE id={id}
    '''

    pg_cur.execute(sql)
    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()


def get_eval_jobs():
    pg_conn, pg_cur = get_pg_connection()

    sql = f'''
    SELECT * FROM eval_job ej
    WHERE "status"='RUNNING' and ("endTime" is NULL or "endTime" > {time.time()})
    ORDER BY "lastRun"
    '''
    pg_cur.execute(sql)

    study_evals = pg_cur.fetchall()
    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()

    return study_evals


def fail_eval(id):
    pg_conn, pg_cur = get_pg_connection()

    sql = f'''
    UPDATE study_evaluation 
    SET status='FAILED'
    WHERE id={id}
    '''

    pg_cur.execute(sql)
    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()


def evaluate(model_image, dicom_path, id):
    r = redis.Redis(host='redis', port=6379, db=0)

    client = docker.from_env()

    volumes = {
        'ai-images': {'bind': '/opt/images', 'mode': 'rw'}
    }

    print('running for image: ', model_image)
    
    stdout = client.containers.run(image=model_image, 
                                   detach=False, 
                                   environment={'FILENAME': dicom_path, 'ID': id}, 
                                   runtime='nvidia', 
                                   network='ai-network',
                                   volumes=volumes)

    out = fromRedis(r, id)

    return out


