import uuid
import traceback
import redis
from typing import Dict, List
import docker
import nvidia_smi

from db import study_db, eval_db
from utils import db_utils
from services import messaging_service, logger_service, orthanc_service
from medaimodels import ModelOutput


def get_eval_ids(model, studies):
    # add db entries for the upcoming study evals
    eval_ids = eval_db.start_study_evaluations(studies, model['id'])

    # reset the failed evaluations status to 'RUNNING'
    eval_ids = eval_ids

    return eval_ids

def get_failed_eval_ids(model):
    failed_evals = eval_db.get_failed_eval_ids(model['id'])
    return eval_db.restart_failed_evals(failed_evals)

def restart_failed_by_exp(experimentId: int):
    eval_ids = eval_db.get_failed_eval_ids_by_exp(experimentId)
    return eval_db.restart_failed_evals(eval_ids)

def evaluate_studies(studies, model, eval_ids):
    # get the orthanc study IDs of all of the studies to be
    # used as the file path for saving dicoms
    try:
        orthanc_ids = [study['orthancStudyId'] for study in studies]
        print('this is what I think orthanc ids are', orthanc_ids)

        results = evaluate(model['image'], orthanc_ids, str(uuid.uuid4()), eval_ids)

        # loop through the results of the classifier and save the classifcation to the DB
        for result, eval_id, orthanc_id in zip(results, eval_ids, orthanc_ids):
            try:
                eval_db.update_eval_status_and_save(result, eval_id)
                model_id = model['id']
                messaging_service.send_notification(f'Finished evaluating {orthanc_id} with model {model_id}', 'new_result')

            except:
                # catch errors and print output
                traceback.print_exc()
                logger_service.log_error(f'updating eval {eval_id} failed', traceback.format_exc())
                # update eval status to FAILED
                eval_db.fail_eval(eval_id)
    except:
        fail_evals(model['id'], eval_ids)

def fail_evals(model_id, eval_ids):
    traceback.print_exc()
    error_message = f'evaluation using model {model_id} failed'
    logger_service.log_error(error_message, traceback.format_exc())

    for eval_id in eval_ids:
        eval_db.fail_eval(eval_id)
    messaging_service.send_notification(error_message, 'eval_failed')

def fail_model(model_id):
    traceback.print_exc()
    error_message = f'evaluation using model {model_id} failed'

    logger_service.log_error(error_message, traceback.format_exc())
    messaging_service.send_notification(error_message, 'eval_failed')

def get_eval_jobs():
    return eval_db.get_eval_jobs()

def add_evals_to_db(orthanc_id, model_id):
    study = study_db.get_study_by_orthanc_id(orthanc_id)
    eval_ids = eval_db.start_study_evaluations([study], model_id)
    logger_service.log(f'evaluation {eval_ids[0]} using model {model_id} started')

    return eval_ids[0]

def evaluate(model_image: str, orthanc_ids: List[str], uuid: str, eval_ids: List[int] = None) -> List[ModelOutput]:
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
    # get redis client
    r = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)
    print('eval info', model_image, orthanc_ids, uuid)

    # get docker client
    client = docker.from_env()

    # define volume for docker images. All downloaded images are linked in this docker volume
    # downloaded studies are mounted in contianers at /opt/images
    volumes = {
        'ai-images': {'bind': '/opt/images', 'mode': 'rw'}
    }

    filenames = ','.join(orthanc_ids)

    # send eval to docker daemon and start container
    # set env variables
    # set runtime to nvidia so that it has a connection to the cuda runtime on host

    runtime = 'nvidia'

    [orthanc_service.download_study_dicom(orthanc_id) for orthanc_id in orthanc_ids]

    container = client.containers.run(image=model_image,
                                      detach=True,
                                      environment={
                                          'FILENAMES': filenames, 
                                          'ID': uuid, 
                                          'NVIDIA_DRIVER_CAPABILITIES': 'compute,utility',
                                          'NVIDIA_VISIBLE_DEVICES': 'all'},
                                      runtime=runtime,
                                      network='ai-network',
                                      volumes=volumes,
                                      shm_size='11G')
    stdout = []

    for line in container.logs(stream=True):
        if eval_ids is not None: 
            line = str(line).replace("b'", "").replace("'", "")

            eval_db.add_stdout_to_eval(eval_ids, line)
            # for eval_id in eval_ids:
            #     messaging.send_model_log(eval_id, line)
            stdout.append(line)
    
    [orthanc_service.delete_study_dicom(orthanc_id) for orthanc_id in orthanc_ids]

    logger_extra = {'stdout': str(stdout)}
    logger_service.log(f'Finished model execution for evaluation {uuid}', logger_extra)
    out = messaging_service.get_result(r, uuid)
    return out

def write_eval_results(results, eval_id):
    eval_db.update_eval_status_and_save(results, eval_id)

def fail_dicom_eval(orthanc_id, model_id, eval_id):
    traceback.print_exc()
    error_message = f'evaluation for study {orthanc_id} using model {model_id} failed'
    logger_service.log_error(error_message, traceback.format_exc())
    # update eval status to FAILED
    eval_db.fail_eval(eval_id)
    messaging_service.send_notification(error_message, 'eval_failed')

def check_gpu():
    try:
        nvidia_smi.nvmlInit()
        return nvidia_smi.nvmlDeviceGetCount() > 0
    except:
        return False

def remove_orphan_evals():
    eval_db.remove_orphan_evals()