from tkinter import E
import uuid
import traceback
from typing import List
from services import messaging_service
from db.models import Model, Study, StudyEvaluation
from db import eval_db, model_db, study_db

import docker
import nvidia_smi

from services import logger_service, orthanc_service
from medaimodels import ModelOutput
import json

from kubernetes import client, config
from pprint import pprint
import json
from uuid import uuid4

JOB_NAMESPACE = "default"
config.load_incluster_config()


def create_evals(model: Model, studies: List[Study]) -> List[int]:
    # add db entries for the upcoming study evals
    eval_ids = eval_db.start_study_evaluations(studies, model.id)
    return eval_ids

def get_failed_eval_ids(model: Model):
    failed_evals = eval_db.get_failed_eval_ids(model.id)
    return eval_db.restart_failed_evals(failed_evals) or []

def reset_failed_evals(experimentId: int) -> List[str]:
    eval_ids = eval_db.get_failed_eval_ids_by_exp(experimentId)
    return eval_db.restart_failed_evals(eval_ids)

def evaluate_studies(studies: List[Study], model: Model, eval_ids: List[int], cpu: bool=False) -> None:
    # get the orthanc study IDs of all of the studies to be
    # used as the file path for saving dicoms
    try:
        orthanc_ids = [study.orthancStudyId for study in studies]
        evaluate(model, orthanc_ids, str(uuid.uuid4()), eval_ids, cpu=cpu)
    except:
        fail_evals(model.id, eval_ids)

def fail_evals(model_id: int, eval_ids: List[int]):
    traceback.print_exc()
    error_message = f'evaluation using model {model_id} failed'
    logger_service.log_error(error_message, traceback.format_exc())

    for eval_id in eval_ids:
        e: StudyEvaluation = eval_db.fail_eval(eval_id)
        messaging_service.send_notification(error_message, 'eval_failed', -1)

def fail_model(model_id: int):
    # TODO: this doesn't seem like it does anything
    traceback.print_exc()
    error_message = f'evaluation using model {model_id} failed'

    logger_service.log_error(error_message, traceback.format_exc())
    messaging_service.send_notification(error_message, 'eval_failed')

def get_eval_jobs():
    return eval_db.get_eval_jobs()

def create_eval(orthanc_id: str, model_id: int) -> int:
    """
    Creates a study eval entry in the database for a given model and orthanc id
    """
    study = study_db.get_study_by_orthanc_id(orthanc_id)
    print('this is the study', study)
    eval_ids = eval_db.start_study_evaluations([study], model_id)
    logger_service.log(f'evaluation {eval_ids[0]} using model {model_id} started')

    return eval_ids[0]

def evaluate_with_quickstart(model: Model, 
                             orthanc_ids: List[str], 
                             db_ids: List[int] = None):

    [orthanc_service.download_study_dicom(orthanc_id) for orthanc_id in orthanc_ids]

    message = {
        'files': orthanc_ids,
        'ids': db_ids,
        'type': 'EVAL'
    }
    print(f'sending message {message} to {str(model.id)}')
    messaging_service.send_message(str(model.id), json.dumps(message))

def evaluate(model: Model, 
             orthanc_ids: List[str], 
             uuid: str, 
             db_ids: List[int] = None, 
             result_queue = messaging_service.EVAL_QUEUE,
             cpu = False) -> List[ModelOutput]:
    """
    Evaluate a study using a model

    Args:
        model_image (str): the tag of the docker that contains the model
        dicom_paths (List[str]): a list of the paths of the dicoms to be evalutated
        eval_id (int): the db ID of the evaluation

    Returns
        :rtype: List[ModelOutput]
        A list of the outputs of the evaluating model
    """

    job = model_db.get_job_by_model(model.id)
    if(job.replicas > 0):
        print('running with quickstart')
        evaluate_with_quickstart(model, orthanc_ids, db_ids)
        return

    # get redis client
    print('eval info', model.image, orthanc_ids, uuid)

    # get docker client
    client = docker.from_env()

    # define volume for docker images. All downloaded images are linked in this docker volume
    # downloaded studies are mounted in contianers at /opt/images
    volumes = {
        'ai-images': {'bind': '/opt/images', 'mode': 'rw'}
    }

    filenames = ','.join(orthanc_ids)
    ids = ''
    if db_ids:
        ids =','.join([str(id) for id in db_ids])

    # send eval to docker daemon and start container
    # set env variables
    # set runtime to nvidia so that it has a connection to the cuda runtime on host

    runtime = 'nvidia' if not cpu else ''

    print('downloading dicoms for studies: ', orthanc_ids)

    [orthanc_service.download_study_dicom(orthanc_id) for orthanc_id in orthanc_ids]


    start_k8_job(model.image, result_queue, filenames, uuid, ids)    


def write_eval_results(results, eval_id: int):
    return eval_db.update_eval_status_and_save(results, eval_id)

def fail_dicom_eval(eval_id):
    traceback.print_exc()
    error_message = f'evaluation for study {eval_id} failed'
    logger_service.log_error(error_message, traceback.format_exc())
    # update eval status to FAILED
    e:StudyEvaluation = eval_db.fail_eval(eval_id)
    messaging_service.send_notification(error_message, 'eval_failed', -1)

def check_gpu():
    try:
        nvidia_smi.nvmlInit()
        return nvidia_smi.nvmlDeviceGetCount() > 0
    except:
        return False

def remove_orphan_evals():
    eval_db.remove_orphan_evals()

def add_stdout_to_eval(ids, stdout):
    eval_db.add_stdout_to_eval(ids, stdout)

def start_k8_job(image, result_queue, filenames, uuid, ids):
    config.load_incluster_config()

    batch_v1 = client.BatchV1Api()

    job_name = f'{image}_{uuid}'
    environment = [
        {'name': 'RESULT_QUEUE', 'value': result_queue},
        {'name': 'FILENAMES', 'value': filenames},
        {'name': 'ID', 'value': uuid},
        {'name': 'RUN_SINGLE', 'value': 'True'},
        {'name': 'DB_IDs', 'value': ids},

    ]

    volume_mounts = [
        {'mount_path': '/opt/images', 'name': 'medai-ai-images'}
    ]

    container = client.V1Container(
            name=image,
            image=image,
            env=environment,
            volume_mounts=volume_mounts
        )
    template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={'name': job_name}),
            spec=client.V1PodSpec(containers=[container]))

    spec = client.V1JobSpec(template=template)

    job = client.V1Job(
        api_version='batch/v1',
        kind='Job',
        metadata=client.V1ObjectMeta(name=job_name),
        spec=spec)

    api_response = batch_v1.create_namespaced_job(
        body=job,
        namespace='default')
    
    return api_response

def set_eval_as_running(eval_id: int):
    eval_db.set_eval_running(eval_id)