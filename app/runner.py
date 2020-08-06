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
import uuid

app = Celery('runner')
app.config_from_object(settings)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    db_queries.remove_orphan_evals()
    db_queries.remove_orphan_studies()
    
    sender.add_periodic_task(10, run_jobs.s(), name='check for jobs every 30 sec')
    sender.add_periodic_task(10, classify_studies.s(15), name='check for new studies every 30 sec')


@app.task
def run_jobs():
    """
    checks the database for current eval jobs and evaluate studies
    """
    # Get currently running jobs
    jobs = db_queries.get_eval_jobs()
    for job in jobs:
        try:
            evaluate_studies.delay(job['modelId'], 1)
        except:
            traceback.print_exc()


@app.task
def classify_studies(batch_size):
    orthanc_studies = utils.get_orthanc_studies()

    db_orthanc_ids = map(lambda x: x['orthancStudyId'], db_queries.get_studies())

    filtered_studies = list(set(orthanc_studies) - set(db_orthanc_ids))

    filtered_studies = filtered_studies[:batch_size]

    modalities = [utils.get_modality(orthanc_id) for orthanc_id in filtered_studies]

    db_queries.insert_studies(filtered_studies)

    if len(filtered_studies) > 0:
        classify_study.delay(filtered_studies, modalities)


@app.task
def evaluate_studies(model_id, batch_size):
    """
    Gets studies from orthanc and evaluates all of the applicable studies using a given model
    
    :param model_id: the database id of the model to use in evalutation
    """
    # get all studies from orthanc
    studies = db_queries.get_studies_for_model(model_id)
    failed_evals = db_queries.get_failed_eval_ids(model_id)

    studies = studies[:batch_size]

    if len(studies) < 1:
        return
    
    # get the appropriate evaluating model
    model = db_queries.get_model(model_id)

    # add db entries for the upcoming study evals
    eval_ids = db_queries.start_study_evaluations(studies, model['id'])
    db_queries.restart_failed_evals(failed_evals, model['id'])

    eval_ids = eval_ids + failed_evals
    try:
        study_paths = [study['orthancStudyId'] for study in studies]

        results = utils.evaluate(model['image'], study_paths, str(uuid.uuid4()), bool(model['hasImageOutput']))
        print(results)

        for result, eval_id in zip(results, eval_ids):
            try:
                db_queries.update_db(result, eval_id)
            except:
                # catch errors and print output
                traceback.print_exc()

                # update eval status to FAILED
                db_queries.fail_eval(eval_id)
    except:
        traceback.print_exc()
        for eval_id in eval_ids:
            db_queries.fail_eval(eval_id)


@app.task
def evaluate_dicom(model_id: str, orthanc_id: str, eval_id: int):
    """
    takes in a image, path to a dicom and a eval id from the db and evaluates the dicom using the image

    :param model_image: the name of the docker image that houses the model
    :param dicom_path: the path on the disk to directory containing the DICOMDIR file
    :param eval_id: the database id of the study evaluation

    """
    try:
        model = db_queries.get_model(model_id)
        study_path, patient_id, modality = utils.get_study(orthanc_id)

        print('here is the study path', study_path)

        # evaluate study and write result to db
        results = utils.evaluate(model['image'], [study_path], str(uuid.uuid4()), bool(model['hasImageOutput']))

        db_queries.update_db(results[0], eval_id)
    except:
        # catch errors and print output
        traceback.print_exc()

        # update eval status to FAILED
        db_queries.fail_eval(eval_id)


@app.task
def classify_study(orthanc_ids, modalities):
    """
    Classifies a study coming from orthanc and saves db entry for the study

    :param classifier_id: the Nid of the db entry for the classifying model
    :param orthanc_id: the study id of the study coming from orthanc
    """
    try:
        # get the classifier model information from the db
        studies = dict()
        orthanc_info = zip(orthanc_ids, modalities)
        ct_scans = []

        for orthanc_id, modality in orthanc_info:
            # download study from orthanc to disk
            study_path, patient_id, modality = utils.get_study(orthanc_id)

            # save the patient id
            db_queries.save_patient_id(patient_id, orthanc_id, modality)

            if modality in studies:
                studies[modality].append(study_path)
            else:
                studies[modality] = [study_path]

        for modality, study_paths in studies.items():
            if modality == 'CT' or utils.check_for_CT(orthanc_id):
                for orthanc_id in study_paths:
                    db_queries.save_study_type(orthanc_id, 'CT')
                    print(f'saved {orthanc_id}')
                continue

            # evaluate the study using classifier model
            print('modality is ',  modality)
            classifier_model = db_queries.get_classifier_model(modality)
            if classifier_model is None:
                classifier_model = db_queries.get_default_model()
                # for orthanc_id in study_paths:
                #     db_queries.remove_study_by_id(orthanc_id)
                # continue

            results = utils.evaluate(classifier_model['image'], study_paths, str(uuid.uuid4()))
            # save a study to the database
            for orthanc_id, result in zip(study_paths, results):
                db_queries.save_study_type(orthanc_id, result['display'])
                print(f'saved {orthanc_id}')


    except:
        # catch errors and print output
        print('classification of study', orthanc_ids, 'failed')
        traceback.print_exc()
        for orthanc_id in orthanc_ids:
            db_queries.remove_study_by_id(orthanc_id)
