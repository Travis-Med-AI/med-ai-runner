"""The main runner for med ai models"""

import traceback
import uuid
from typing import List
from collections import defaultdict
from celery import Celery

import db_queries
import utils
import settings
import logger
import messaging


app = Celery('runner')
app.config_from_object(settings)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """set up celery beat tasks"""
    db_queries.remove_orphan_evals()
    db_queries.remove_orphan_studies()

    sender.add_periodic_task(10, run_jobs.s(), name='check for jobs every 10 sec')
    sender.add_periodic_task(10, classify_studies.s(5), name='check for new studies every 10 sec')


@app.task
def run_jobs():
    """
    checks the database for current eval jobs and evaluates studies
    """
    # Get currently running jobs
    jobs = db_queries.get_eval_jobs()
    for job in jobs:
        try:
            evaluate_studies.delay(job['modelId'], 1)
        except Exception as e:
            logger.log_error(f'{job.id} failed', traceback.format_exc())
            traceback.print_exc()


@app.task
def classify_studies(batch_size: int):
    """
    This is run by the beat. It looks for new studies in orthanc and then classifies the study type

    Args:
        batch_size (int): the number of images to feed into the classifier at a time
    """

    # get orthanc study ids from orthanc
    orthanc_studies = utils.get_orthanc_studies()

    # get ids of studies that have already been processed and saved to the db
    db_orthanc_ids = map(lambda x: x['orthancStudyId'], db_queries.get_studies())

    # filter out studies that have already been evaluated
    # TODO: this should be done with a db call the dose WHERE NOT IN ()
    filtered_studies = list(set(orthanc_studies) - set(db_orthanc_ids))
    filtered_studies = filtered_studies[:batch_size]

    # get the modalities for all the orthanc studies
    modalities = [utils.get_modality(orthanc_id) for orthanc_id in filtered_studies]

    # insert records in the db for all of the downloaded orthanc studies
    db_queries.insert_studies(filtered_studies)

    # classify the downloaded studies
    if len(filtered_studies) > 0:
        classify_study.delay(filtered_studies, modalities)


@app.task
def evaluate_studies(model_id: List[str], batch_size: int):
    """
    Gets studies from orthanc and evaluates all of the applicable studies using a given model

    Args:
        model_id (:obj:`list`): A list of study IDs from orthanc
        batch_size (int): the number of images to process at a time
    """
    try:

        # get all studies from orthanc
        studies = db_queries.get_studies_for_model(model_id)
        failed_evals = db_queries.get_failed_eval_ids(model_id)
        # trim studies down to batch size
        studies = studies[:batch_size]

        if len(studies) < 1:
            return


        # get the appropriate evaluating model
        model = db_queries.get_model(model_id)

        # add db entries for the upcoming study evals
        eval_ids = db_queries.start_study_evaluations(studies, model['id'])

        # reset the failed evaluations status to 'RUNNING'
        db_queries.restart_failed_evals(failed_evals)
        eval_ids = eval_ids + failed_evals

        try:
            # get the orthanc study IDs of all of the studies to be
            # used as the file path for saving dicoms
            orthanc_ids = [study['orthancStudyId'] for study in studies]

            # evaluate the studies using the classifier
            results = utils.evaluate(model['image'], orthanc_ids, str(uuid.uuid4()), eval_ids)

            # loop through the results of the classifier and save the classifcation to the DB
            for result, eval_id, orthanc_id in zip(results, eval_ids, orthanc_ids):
                try:
                    db_queries.update_db(result, eval_id)
                    messaging.send_notification(f'Finished evaluating {orthanc_id} with model {model_id}', 'new_result')

                except:
                    # catch errors and print output
                    traceback.print_exc()
                    logger.log_error(f'updating eval {eval_id} failed', traceback.format_exc())
                    # update eval status to FAILED
                    db_queries.fail_eval(eval_id)
        except Exception as e:
            traceback.print_exc()
            error_message = f'evaluation {eval_id} using model {model_id} failed'
            logger.log_error(error_message, traceback.format_exc())

            for eval_id in eval_ids:
                db_queries.fail_eval(eval_id)
            messaging.send_notification(error_message, 'eval_failed')
            
    except Exception as e:
        traceback.print_exc()
        error_message = f'evaluation {eval_id} using model {model_id} failed'

        logger.log_error(error_message, traceback.format_exc())
        messaging.send_notification(error_message, 'eval_failed')

@app.task
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
        study = db_queries.get_study_by_orthanc_id(orthanc_id)
        eval_ids = db_queries.start_study_evaluations([[study['id']]], model_id)
        eval_id = eval_ids[0]
        logger.log(f'evaluation {eval_id} using model {model_id} started')

        # get the model from the database
        model = db_queries.get_model(model_id)

        # download the study from orthanc
        study_path, _, _ = utils.get_study(orthanc_id)

        # evaluate study and write result to db
        results = utils.evaluate(model['image'], [study_path], str(uuid.uuid4()), eval_ids)
        db_queries.update_db(results[0], eval_id)
        messaging.send_notification(f'Finished evaluating {orthanc_id} with model {model_id}', 'new_result')
    
    except Exception as e:
        # catch errors and print output
        traceback.print_exc()
        error_message = f'evaluation for study {orthanc_id} using model {model_id} failed'
        logger.log_error(error_message, traceback.format_exc())
        # update eval status to FAILED

        db_queries.fail_eval(eval_id)
        messaging.send_notification(error_message, 'eval_failed')


@app.task
def classify_study(orthanc_ids: List[int], modalities: List[str]):
    """
    Classifies a study coming from orthanc and saves db entry for the study

    Args:
        classifier_id (int): the ID of the db entry for the classifying model
        orthanc_id (int): the study id of the study coming from orthanc
    """
    try:
        # set up dictionary that splits studies by modality as modality: list(study_path)
        studies = defaultdict(list)

        for orthanc_id, modality in zip(orthanc_ids, modalities):
            # download study from orthanc to disk
            study_path, patient_id, modality = utils.get_study(orthanc_id)

            # save the patient id
            db_queries.save_patient_id(patient_id, orthanc_id, modality)

            # add studies to modality dictionary
            studies[modality].append(study_path)

        # TODO: seems like a lot of nested loops here...revisit and optimize
        for modality, study_paths in studies.items():

            # Check to see if the case is a CT scan by seeing if the dicom modality is 'CT'
            # or the DICOMDIR has multiple slices
            # TODO: come up with a better solution for identifying CT scans
            if modality == 'CT' or utils.check_for_ct(study_paths[0]):
                for orthanc_id in study_paths:
                    db_queries.save_study_type(orthanc_id, 'CT')
                    messaging.send_notification(f'Study {orthanc_id} ready', 'study_ready')
                continue

            # evaluate the study using classifier model
            classifier_model = db_queries.get_classifier_model(modality)

            # check to see if there is currently a classifier set for the given modality
            # if not just get the default one from the db
            if classifier_model is None:
                classifier_model = db_queries.get_default_model()

            # run studies through the classifier model
            results = utils.evaluate(classifier_model['image'], study_paths, str(uuid.uuid4()))

            # save the results of classifcation to the database
            # TODO: optimize with BULK insert
            for orthanc_id, result in zip(study_paths, results):
                db_queries.save_study_type(orthanc_id, result['display'])
                messaging.send_notification(f'Study {orthanc_id} ready', 'study_ready')

    except Exception as e:
        # catch errors and print output
        print('classification of study', orthanc_ids, 'failed')
        traceback.print_exc()
        logger.log_error(f'classfying {orthanc_ids} failed', traceback.format_exc())
        # remove studies from the db that failed on classfication
        for orthanc_id in orthanc_ids:
            db_queries.remove_study_by_id(orthanc_id)
