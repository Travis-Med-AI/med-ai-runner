"""The main runner for med ai models"""

import traceback
import uuid
from typing import List
from collections import defaultdict
from utils.db_utils import close_db_pool, close_rabbit, init_db, init_rabbit
from services import messaging_service
from celery import Celery
import time
from celery.signals import worker_process_init, worker_process_shutdown


import settings
from services import logger_service, classifier_service, eval_service, experiment_service, model_service, orthanc_service, study_service
from utils import utils as uP

runner = Celery('runner')
runner.config_from_object(settings.Settings())
runner.control.purge()
# eval_service.remove_orphan_evals()
# study_service.remove_orphan_studies()
# model_service.turn_off_all_models()
# messaging_service.start_result_queue()

@worker_process_init.connect
def init_worker(**kwargs):
    init_db()
    init_rabbit()
    print('starting worker')

@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    close_db_pool()
    close_rabbit()

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
    print(f'found {len(jobs)} jobs to run')
    for job in jobs:
        try:
            evaluate_studies.delay(job.modelId, 1, job.cpu)
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

    new_studies = study_service.get_new_studies(batch_size)

    # check to make sure there are studies
    if len(new_studies) < 1:
        print('no new studies found')
        return

    # download study metadata and classify
    try:
        print('classifying', new_studies)
        # get study metadata
        study_metadata = study_service.save_study_metadata(new_studies)
        # loop through and classify all studies
        classifier_service.classify_studies(study_metadata)

    except Exception as e:
        classifier_service.fail_classification(new_studies)


@runner.task
def run_experiments(batch_size: int):
    """
    Monitors db for active experiments and runs them
    """
    print(f'running experiments with batch size of {batch_size}')

    # get experiments
    experiments = experiment_service.get_running_experiments()
    
    print(f'found {len(experiments)} experiments')
    # run experiments
    for experiment in experiments:
        # check if the experiment is done and update as finished
        if experiment_service.check_if_experiment_complete(experiment):
            experiment_service.finish_experiment(experiment)
            continue
        # get model
        model = model_service.get_model(experiment.modelId)
        # reset any failed evals associated with the experiment
        eval_service.reset_failed_evals(experiment.id)
        studies = experiment_service.get_experiment_studies(experiment.id)
        # create batch of studies and check if there are already running studies
        batch = studies[:batch_size]
        running_studies = experiment_service.get_running_evals_by_exp(experiment.id)
        print(running_studies)
        print(batch)
        # this makes it so there are only 5 evaluations
        if len(batch) > 0 and len(running_studies) < 5:
            experiment_service.run_experiment(batch, model, experiment)
    print('finished experiment task')


@runner.task
def evaluate_studies(model_id: int, batch_size: int, cpu: bool = False):
    """
    Gets studies from orthanc and evaluates all of the applicable studies using a given model

    Args:
        model_id (:obj:`list`): A list of study IDs from orthanc
        batch_size (int): the number of images to process at a time
    """
    try:    
        # get all studies
        model = model_service.get_model(model_id)
        studies = study_service.get_studies_for_model(model_id, batch_size)
        # exit if no studies
        if len(studies) < 1:
            return
        # get the appropriate evaluating model
        print(f'found {len(studies)} studies for model {model.displayName}')
        # create evaluations for all the studies and get their ids
        failed_evals = eval_service.get_failed_eval_ids(model)
        eval_ids = eval_service.create_evals(model, studies) + failed_evals
        # evaluate all studies with the model
        eval_service.evaluate_studies(studies, model, eval_ids, cpu)
    except Exception as e:
        eval_service.fail_model(model_id)
    print('finished evaluate studies')

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
        print('evaluating dicom ', orthanc_id)
        # create eval entry for the incoming study
        eval_id = eval_service.create_eval(orthanc_id, model_id)
        print('eval id is: ', eval_id)
        # get the model from the database
        model = model_service.get_model(model_id)
        # download the study from orthanc
        metadata = orthanc_service.get_study_metadata(orthanc_id)
        # evaluate study
        eval_service.evaluate(model, [metadata.orthanc_id], str(uuid.uuid4()), [eval_id])
    except Exception as e:
        # catch errors and print output
        eval_service.fail_dicom_eval(eval_id)
    print('finished evaluate dicom')

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
        # getting unstarted models
        jobs = model_service.get_jobs_to_quickstart()
        if len(jobs) < 1:
            return
        print(f'found the following models to quickstart: {jobs}')
        # quickstart model
        model_service.quickstart_model(jobs[0])

    except Exception as e:
        print('quickstart failed')
        traceback.print_exc()
    
@runner.task
def purge_orthanc():
    """
    purges old studies from orthanc
    """
    try:
        print('purging orthanc studies')
        # getting unstarted models
        one_day_ago = time.time() - (24 * 60 * 60 * 1000)
        old_study_ids = study_service.get_old_studies(one_day_ago)
        print('found the following orthanc studies to delete', old_study_ids)
        orthanc_service.delete_from_orthanc(old_study_ids)

    except Exception as e:
        print('purge orthanc failed')
        traceback.print_exc()