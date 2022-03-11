from typing import List
from xmlrpc.client import boolean

from sqlalchemy import false
from db.model_db import ModelDB
from db.models import Model
import docker
from services import messaging_service, settings_service

model_db = ModelDB()

def get_model(model_id: int) -> Model:
    return model_db.get_model(model_id)

def get_models_to_quickstart():
    models:List[Model] = model_db.get_models_to_quickstart()
    client = docker.from_env()
    containers = [container.attrs['Config']['Image'] for container in client.containers.list()]
    models_to_start = []
    for model in models:
        if not model.quickStartRunning:
            models_to_start.append(model)
            continue
        if model.image not in containers:
            print(model.image, containers)
            models_to_start.append(model)
    return models_to_start

def quickstart_model(model: Model, cpu: boolean = False):
    try:

        volumes = {
            'ai-images': {'bind': '/opt/images', 'mode': 'rw'}
        }
        client = docker.from_env()

        runtime = 'nvidia' if not cpu else ''
        model_db.mark_models_as_quickstarted([model.id])
        print(f'starting docker container for {model}')

        container = client.containers.run(image=model.image,
                                        detach=True,
                                        environment={
                                            'ID': model.id,
                                            'QUEUE': model.id,
                                            'RESULT_QUEUE': messaging_service.EVAL_QUEUE,
                                            'NVIDIA_DRIVER_CAPABILITIES': 'compute,utility',
                                            'RABBITMQ_URL': settings_service.get_rabbitmq_url(),
                                            'NVIDIA_VISIBLE_DEVICES': 'all'},
                                        runtime=runtime,
                                        network='ai-network',
                                        volumes=volumes,
                                        shm_size='12G')
        print('started container. now waiting for stuff')
        for line in container.logs(stream=True):
            line = str(line).replace("b'", "").replace("'", "")
            print(f'docker output: {line}')
        print(f'stopping model {model.id}')
        model_db.mark_model_as_stopped(model.id)
    except:
        model_db.mark_model_as_stopped(model.id)

def turn_off_all_models():
    return model_db.stop_all_models()