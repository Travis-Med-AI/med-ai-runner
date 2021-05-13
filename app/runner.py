"""The main runner for med ai models"""

import traceback
import uuid
from typing import List
from collections import defaultdict
from celery import Celery
import time

import settings
from services import logger_service, classifier_service, eval_service, experiment_service, messaging_service, model_service, orthanc_service, study_service
from utils import utils as u
import multiprocessing

runner = Celery('runner')
runner.config_from_object(settings)
runner.control.purge()
eval_service.remove_orphan_evals()
study_service.remove_orphan_studies()
model_service.turn_off_all_models()
messaging_service.start_result_queue()


@runner.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """set up celery beat tasks"""

    print(runner.tasks.keys())



@runner.task
def run_jobs():
    """
    checks the database for current eval jobs and evaluates studies
    """
    # Get currently running jobs

    print('runnning jobs')
    jobs = eval_service.get_eval_jobs()
    for job in jobs:
        try:
            evaluate_studies.delay(job['modelId'], 1)
        except Exception as e:
            logger_service.log_error(f'{job.id} failed', traceback.format_exc())
            traceback.print_exc()


@runner.task
def classify_studies(batch_size: int):
    """
    This is run by the beat. It looks for new studies in orthanc and then classifies the study type

    Args:
        batch_size (int): the number of images to feed into the classifier at a time
    """
    print('classifying studies')

    t0 = time.time()
    new_studies = study_service.get_new_studies(batch_size)

    # classify the downloaded studies
    if len(new_studies) < 1:
        print('no new studies found')
        return
    t1 = time.time()
    print(f'getting studies took for classification  {t1-t0}')

    t0 = time.time()
    # get the modalities for all the orthanc studies
    modalities = [orthanc_service.get_modality(study) for study in new_studies]
    t1 = time.time()
    print(f'getting modalities took {t1-t0}') 
    try:
        t0 = time.time()

        print('classifying', new_studies)
        # set up dictionary that splits studies by modality as modality: list(study_path)
        studies = study_service.get_study_modalities(new_studies, modalities)
        t1 = time.time()
        print(f'getting study modalities took {t1-t0}') 
        # loop through and classify all studies

        t0 = time.time()

        classifier_service.classify_studies(studies)
        t1 = time.time()
        print(f'classifying took {t1-t0}') 

    except Exception as e:
        classifier_service.fail_classification(new_studies)


@runner.task
def run_experiments(batch_size: int):
    """
    Monitors db for active experiments and runs them
    """
    print('running experiments')

    # get experiments
    experiments = experiment_service.get_running_experiments()

    # run experiments
    for experiment in experiments:
        messaging_service.send_notification(f'Started experiment {experiment["name"]}', 
                                             'experiment_started')
        # restart failed evaluations
        eval_service.restart_failed_by_exp(experiment['id'])
        # get experiment studies
        studies = experiment_service.get_experiment_studies(experiment['id'])
        # get model
        model = model_service.get_model(experiment['modelId'])
        batch = studies[:batch_size]
        experiment_service.run_experiment(batch, dict(model), dict(experiment))


@runner.task
def evaluate_studies(model_id: List[str], batch_size: int):
    """
    Gets studies from orthanc and evaluates all of the applicable studies using a given model

    Args:
        model_id (:obj:`list`): A list of study IDs from orthanc
        batch_size (int): the number of images to process at a time
    """
    try:
        print(f'evaluating studies for {model_id}')

        # get all studies
        studies = study_service.get_studies_for_model(model_id, batch_size)

        # exit if no studies
        if len(studies) < 1:
            return

        # get the appropriate evaluating model
        model = model_service.get_model(model_id)

        # get ids of study evaluations
        eval_ids = eval_service.get_eval_ids(model, studies) + eval_service.get_failed_eval_ids(model)

        eval_service.evaluate_studies(studies, model, eval_ids)
            
    except Exception as e:
        eval_service.fail_model(model_id)


@runner.task
def evaluate_dicom(model_id: int, orthanc_id: str):
    """
    takes in a image, path to a dicom and a eval id
    from the db and evaluates the dicom using the image

    Args:
        model_id (int): the id of the database model
        dicom_path (str): the path on the disk to the directory containing the DICOMDIR file
        eval_id (int): the database id of the study evaluation that has already been saved by caller
    """
    try:
        print('evaluating dicom')
        eval_id = eval_service.add_evals_to_db(orthanc_id, model_id)
        print('getting model')
        # get the model from the database
        model = model_service.get_model(model_id)

        print('downloading dicom')
        # download the study from orthanc
        study_path, _, _, _, _ = orthanc_service.get_study(orthanc_id)
        print('evaluating...')
        # evaluate study
        eval_service.evaluate(model, [study_path], str(uuid.uuid4()), [eval_id])

        
    except Exception as e:
        # catch errors and print output
        eval_service.fail_dicom_eval(orthanc_id, model_id, eval_id)

@runner.task
def quickstart_models():
    """
    takes in a image, path to a dicom and a eval id
    from the db and evaluates the dicom using the image

    Args:
        model_id (int): the id of the database model
        dicom_path (str): the path on the disk to the directory containing the DICOMDIR file
        eval_id (int): the database id of the study evaluation that has already been saved by caller
    """
    try:
        print('running quickstart')
        # getting unstarted models
        models = model_service.get_models_to_quickstart()
        print(f'found the following models to quickstart: {models}')
        # start models
        if len(models) > 0:
            model_service.quickstart_model(models[0])

    except Exception as e:
        print('quickstart failed')
        traceback.print_exc()

