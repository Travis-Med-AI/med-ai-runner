from celery.schedules import crontab


CELERY_BROKER_URL = 'amqp://guest:guest@rabbitmq:5672'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULE = {
    'hello': {
        'task': 'app.tasks.hello',
        'schedule': crontab()  # execute every minute
    }
}