import os
from celery import Celery, shared_task
import settings
import docker


app = Celery('runner')
app.config_from_object(settings)
# app.autodiscover_tasks(['evaluate_dicom'])

# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
    # Calls every 10 seconds.
    # sender.add_periodic_task(60.0, evaluate_dicom.s('example', '/home/travis/dev/med_ai_runner/example.dcm'), name='add every 10')

@app.task
def evaluate_dicom(model_image, dicom_path):
    print('start')

    client = docker.from_env()

    filename = 'example.dcm'

    container_path = f'/opt/{filename}'

    print(dicom_path)

    mounts = [docker.types.Mount(container_path, dicom_path, type="bind" )]

    stdout = client.containers.run(image=model_image, mounts=mounts, detach=False, environment={'FILENAME': filename}, runtime='nvidia')

    print(stdout)

    print('done')