import traceback

from db import experiment_db
from services import eval_service, logger_service, messaging_service

def get_running_experiments():
    return experiment_db.get_running_experiments()


def get_experiment_studies(experiment_id):
    return experiment_db.get_studies_for_experiment(experiment_id)


def run_experiment(model, studies):
    """
    takes in model  and studies and runs through experiment
    """
    
    eval_ids = eval_service.get_eval_ids(model, studies)

    eval_service.evaluate_studies(studies, model, eval_ids)

def finish_experiment(experiment):
    """
    """
    experiment_db.set_experiment_complete(experiment['id'])
    messaging_service.send_notification(f'Completed experiment {experiment["name"]}', 'experiment_finished')

def fail_experiment(experiment):
    """
    """
    messaging_service.send_notification(f'Failed experiment {experiment["name"]}', 'experiment_failed')
    experiment_db.set_experiment_failed(experiment['id'])
    traceback.print_exc()
    experiment_id = experiment['id']
    logger_service.log_error(f'experiment {experiment_id} failed', traceback.format_exc())