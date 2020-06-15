from celery.schedules import crontab


broker_url = 'amqp://guest:guest@rabbitmq:5672'
result_backend = 'redis://redis:6379'
worker_concurrency=10