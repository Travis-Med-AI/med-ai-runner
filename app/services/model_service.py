from db import model_db
import docker
from services import messaging_service, settings_service


def get_model(model_id):
    return model_db.get_model(model_id)

def get_models_to_quickstart():
    return model_db.get_models_to_quickstart()

def quickstart_model(model):

    volumes = {
        'ai-images': {'bind': '/opt/images', 'mode': 'rw'}
    }
    client = docker.from_env()

    runtime = 'nvidia'
    model_db.mark_models_as_quickstarted([model['id']])
    print(f'starting docker container for {model}')

    container = client.containers.run(image=model['image'],
                                      detach=True,
                                      environment={
                                        'ID': model['id'],
                                        'QUEUE': model['id'],
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
    
    model_db.mark_model_as_stopped(model['id'])

def turn_off_all_models():
    return model_db.stop_all_models()