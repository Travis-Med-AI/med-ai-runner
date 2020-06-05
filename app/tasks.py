import docker
import os
from celery import Celery
from runner import app
from celery import shared_task


@app.task
def evaluate_dicom(self, model_image, dicom_path):
    # client = docker.from_env()

    # model_image_name = 'example'

    # filepath = f'{os.path.dirname(os.path.abspath(__file__))}/example.dcm'
    # container_path = '/opt/example.dcm'

    # mounts = [docker.types.Mount(container_path, filepath, type="bind" )]

    # stdout = client.containers.run(image=model_image_name, mounts=mounts, detach=False)
    # print(stdout)

    print('running tasks')