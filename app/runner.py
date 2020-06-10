import os
from celery import Celery, shared_task
import settings
import docker
import redis
import numpy as np
import json
import requests
import utils
import traceback

app = Celery('runner')
app.config_from_object(settings)

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(30, run_jobs.s(), name='check for jobs every 30 sec')


@app.task
def run_jobs():
    jobs = utils.get_eval_jobs()

    print('running jobs: ', jobs)

    for job in jobs:
        try:
            evaluate_studies.delay(job['modelId'])
        except Exception as e:
            print('job', job['id'], 'failed')
            print(e)
            traceback.print_exc()

@app.task
def evaluate_studies(model_id):
    studies = list(requests.get('http://orthanc:8042/studies').json())
    processed = utils.get_study_ids(model_id)

    filtered_studies = set(studies).symmetric_difference(set(processed))
    if len(filtered_studies) == 0:
        return
    
    model = utils.get_model(model_id)
    study_ids = utils.start_study_evaluations(filtered_studies, model['id'])
    
    for study, study_id in zip(filtered_studies, study_ids):
        try:
            print(study_id)
            study_path = utils.get_study(study)
            out = utils.evaluate(model['image'], study_path, study)
            utils.update_db(out, study_id)
        except Exception as e:
            print('evaluation for study', study, 'failed')
            traceback.print_exc()
            print(e)
            utils.fail_eval(study_id)


@app.task
def evaluate_dicom(model_image, dicom_path, id):
    try:
        output = utils.evaluate(model_image, dicom_path, id)
        utils.update_db(output, id)
    except Exception as e:
        print('it failed')
        print(e)
        utils.fail_eval(id)
        traceback.print_exc()

