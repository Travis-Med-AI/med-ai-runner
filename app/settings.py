"""Celery settings for runner"""
from services import settings_service
import os 

class Settings():
    def __init__(self):
        rabbitmq_url = os.getenv('RABBIT_MQ_URL') or 'pyamqp://guest:guest@rabbitmq:5672'
        redis_url = os.getenv('REDIS_URL') or 'redis://redis:6379'
        orthanc_url = os.getenv('ORTHANC_URL') or 'http://orthanc:8042'
        postgres_url = os.getenv('POSTGRES_URL') or "postgresql://test:test@postgres-db:5432/ai"
        default_settings = {
            'rabbitmqUrl': rabbitmq_url,
            'redisUrl': redis_url,
            'orthancUrl': orthanc_url,
            'postgresUrl': postgres_url
        }
        self.broker_url = default_settings['rabbitmqUrl']
        self.result_backend = default_settings['redisUrl']
    
    broker_pool_limit = 1

    task_create_missing_queues  = True
    beat_schedule = {
    'run_jobs': {
            'task': 'runner.run_jobs',
            'schedule': 3,  # every 15 sec for test,
            'options': {'queue' : 'celery'},  # options are mapped to apply_async options
        },
        'classify_studies': {
            'task': 'runner.classify_studies',
            'schedule': 15,  # every 15 sec for test,
            'args': (30,),
            'options': {'queue' : 'celery'},  # options are mapped to apply_async options
        },
        'run_experiments': {
            'task': 'runner.run_experiments',
            'args': (5,),
            'schedule': 15,  # every 15 sec for test
            'options': {'queue' : 'celery'},  # options are mapped to apply_async options
        },
        'quickstart_models': {
            'task': 'runner.quickstart_models',
            'schedule': 15,  # every 15 sec for test
            'options': {'queue' : 'celery'},  # options are mapped to apply_async options
        },
        'delete_old_orthanc': {
            'task': 'runner.purge_orthanc',
            'schedule': 15,  # every 15 sec for test
            'options': {'queue' : 'celery'},  # options are mapped to apply_async options
        },
    }