import traceback
from typing import Dict, List
from services import messaging_service
from db import experiment_db


from db.models import Experiment, Study
from services import eval_service, logger_service



def get_running_experiments():
    return experiment_db.get_running_experiments()


def get_experiment_studies(experiment_id: int) -> List[Study]:
    return experiment_db.get_studies_for_experiment(experiment_id)


def finish_experiment(experiment: Experiment):
    """
    """
    experiment_db.set_experiment_complete(experiment.id)
    messaging_service.send_notification(f'Completed experiment {experiment.name}', 'experiment_finished', experiment.userId)


def check_if_experiment_complete(experiment: Experiment) -> bool:
    evals_left = experiment_db.get_studies_for_experiment(experiment.id)
    evals_running = experiment_db.get_running_studies_for_experiment(experiment.id)
    return len(evals_left) + len(evals_running) < 1


def fail_experiment(experiment: Experiment):
    """
    """
    messaging_service.send_notification(f'Failed experiment {experiment.name}', 'experiment_failed', experiment.userId)
    experiment_db.set_experiment_failed(experiment.id)
    traceback.print_exc()
    messaging_service.log_error(f'experiment {experiment.id} failed', traceback.format_exc())


def get_running_evals_by_exp(experimentId: int) -> List[Dict]:
    return experiment_db.get_running_studies_for_experiment(experimentId)


def run_experiment(studies, model, experiment):
    """
    """
    try:
        print('\n\n\nstarting experiment batch\n\n\n')
        # run experiment
        eval_ids = eval_service.create_evals(model, studies)

        eval_service.evaluate_studies(studies, model, eval_ids)
        # finish experiment and set it as completed

    except Exception as e:
        # fail_experiment(experiment)
        print('lol something failed on experiment')
