"""Celery settings for runner"""

broker_url = 'amqp://guest:guest@rabbitmq:5672'
result_backend = 'redis://redis:6379'
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
        'args': (1,),
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