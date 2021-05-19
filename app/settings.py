"""Celery settings for runner"""
from services import settings_service

class Settings():
    def __init__(self):
        settings = settings_service.get_settings()
        self.broker_url = settings['rabbitmqUrl']
        self.result_backend = settings['redisUrl']

    task_create_missing_queues  = True
    beat_schedule = {
    'run_jobs': {
            'task': 'runner.run_jobs',
            'schedule': 15,  # every 15 sec for test,
            'options': {'queue' : 'celery'},  # options are mapped to apply_async options
        },
        'classify_studies': {
            'task': 'runner.classify_studies',
            'schedule': 15,  # every 15 sec for test,
            'args': (5,),
            'options': {'queue' : 'celery'},  # options are mapped to apply_async options
        },
        'run_experiments': {
            'task': 'runner.run_experiments',
            'args': (1,),
            'schedule': 15,  # every 15 sec for test
            'options': {'queue' : 'celery'},  # options are mapped to apply_async options
        },
        'quickstart_models': {
            'task': 'runner.quickstart_models',
            'schedule': 15,  # every 15 sec for test
            'options': {'queue' : 'no_gpu'},  # options are mapped to apply_async options
        },
    }