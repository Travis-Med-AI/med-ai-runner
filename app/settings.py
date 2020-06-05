from celery.schedules import crontab


broker_url = 'amqp://guest:guest@rabbitmq:5672'
# CELERY_ACCEPT_CONTENT = ['application/json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'

# beat_scehdule = {
#     'hello': {
#         'task': 'app.tasks.evaluate_dicom',
#         'schedule': crontab()  # execute every minute
#     }
# }