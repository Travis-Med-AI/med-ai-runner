import docker
import os
from celery import Celery
from runner import app
from celery import shared_task


@app.task
def evaluate_dicom(model_image, dicom_path):
    print('start')

    client = docker.from_env()

    model_image_name = 'example'

    filepath = f'{os.path.dirname(os.path.abspath(__file__))}/example.dcm'

    print(filepath)
    container_path = '/opt/example.dcm'

    # mounts = [docker.types.Mount(container_path, filepath, type="bind" )]

    # stdout = client.containers.run(image=model_image_name, mounts=mounts, detach=False)

    # output = open('output.txt', 'w')
    # output.write(stdout)
    # output.close()

    # print(stdout)

    # print('done')
