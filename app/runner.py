import os
from celery import Celery
import settings

app = Celery('runner')
app.config_from_object(settings)
# app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))