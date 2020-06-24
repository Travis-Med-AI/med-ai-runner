from celery.schedules import crontab


broker_url = 'amqp://guest:guest@rabbitmq:5672'
result_backend = 'redis://redis:6379'
worker_concurrency=3
# task_routes = ([
#     ('runner.run_jobs', {'queue': 'jobs'}),
#     ('runner.classify_studies', {'queue': 'classifiers'}),
#     ('runner.classify_study', {'queue': 'classifiers'}),
#     ('runner.evaluate_dicom', {'queue': 'jobs'}),
#     ('runner.evaluate_studies', {'queue': 'jobs'}),
# ])