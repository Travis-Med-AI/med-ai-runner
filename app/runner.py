import os
from celery import Celery, shared_task
import settings
import docker
import redis
import numpy as np
import json
import requests
import utils
import db_queries
import traceback

app = Celery('runner')
app.config_from_object(settings)

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(30, run_jobs.s(), name='check for jobs every 30 sec')

    sender.add_periodic_task(30, classify_studies.s(), name='check for new studies every 30 sec')


@app.task
def run_jobs():
    """
    checks the database for current eval jobs and evaluate studies
    """
    # Get currently running jobs
    jobs = db_queries.get_eval_jobs()
    for job in jobs:
        try:
            evaluate_studies.delay(job['modelId'], 10)
        except Exception as e:
            print('job', job['id'], 'failed')
            print(e)
            traceback.print_exc()


@app.task
def classify_studies():
    orthanc_studies = utils.get_orthanc_studies()

    db_orthanc_ids = map(lambda x: x['orthancStudyId'], db_queries.get_studies())

    filtered_studies = list(set(orthanc_studies) - set(db_orthanc_ids))

    classifier_models = db_queries.get_classifier_models()

    # TODO: make this work for every classifier model
    model = classifier_models[0]

    print(f'retreived {len(filtered_studies)} studies from orthanc')

    db_queries.insert_studies(filtered_studies)

    for study in filtered_studies:
        classify_study.delay(model['id'], study)



@app.task
def evaluate_studies(model_id, batch_size):
    """
    Gets studies from orthanc and evaluates all of the applicable studies using a given model
    
    :param model_id: the database id of the model to use in evalutation
    """
    # get all studies from orthanc
    studies = db_queries.get_studies_for_model(model_id)

    studies = studies[:batch_size]

    print(f'received {len(studies)} studies to evaluate')
    
    # get the appropriate evaluating model
    model = db_queries.get_model(model_id)

    # add db entries for the upcoming study evals
    eval_ids = db_queries.start_study_evaluations(studies, model['id'])

    for study, eval_id in zip(studies, eval_ids):
        try:
            # download study from orthanc
            study_path = utils.get_study(study['orthancStudyId'])

            # evaluate study and write result to db
            out = utils.evaluate(model['image'], study_path, study['orthancStudyId'])
            db_queries.update_db(out, eval_id)
        except:
            # catch errors and print output
            print('evaluation for study', study['orthancStudyId'], 'failed')
            traceback.print_exc()

            # update eval status to FAILED
            db_queries.fail_eval(eval_id)


@app.task
def evaluate_dicom(model_image: str, dicom_path: str, eval_id: int):
    """
    takes in a image, path to a dicom and a eval id from the db and evaluates the dicom using the image

    :param model_image: the name of the docker image that houses the model
    :param dicom_path: the path on the disk to directory containing the DICOMDIR file
    :param eval_id: the database id of the study evaluation

    """
    try:
        # evaluate study and write result to db
        output = utils.evaluate(model_image, dicom_path, eval_id)
        db_queries.update_db(output, eval_id)
    except Exception as e:
        # catch errors and print output
        print('evaluation', eval_id, 'failed')
        print(e)
        traceback.print_exc()

        # update eval status to FAILED
        db_queries.fail_eval(eval_id)


@app.task
def classify_study(classifier_id:int, orthanc_id:int):
    """
    Classifies a study coming from orthanc and saves db entry for the study

    :param classifier_id: the id of the db entry for the classifying model
    :param orthanc_id: the study id of the study coming from orthanc
    """
    try:

        # get the classifier model information from the db
        classifier_model = db_queries.get_model(classifier_id)

        # download study from orthanc to disk
        study_path = utils.get_study(orthanc_id)

        # evaluate the study using classifier model
        study_type = utils.evaluate(classifier_model['image'], study_path, f'{orthanc_id}-study', stringOutput=True)
        print(f'finished evaluating{orthanc_id}')
        # save a study to the database
        db_queries.save_study_type(orthanc_id, study_type)
        print(f'saved {orthanc_id}')

    except:
        # catch errors and print output
        print('classification of study', orthanc_id, 'failed')
        traceback.print_exc()
