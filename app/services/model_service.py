from typing import List
from xmlrpc.client import boolean
from numpy import imag

from sqlalchemy import false
from services import messaging_service
from db import model_db
from db.models import EvalJob, Model
import docker
from services import settings_service
from kubernetes import client, config


def sanitize_model_name(name):
    return ''.join(e for e in name if (e.isalnum() or e=='-')) + 'x'

def get_model(model_id: int) -> Model:
    return model_db.get_model(model_id)

def get_jobs_to_quickstart():
    jobs:List[EvalJob] = model_db.get_jobs_to_quickstart()
    batch_v1 = client.AppsV1Api()
    # Check for deployment
    deploys = batch_v1.list_deployment_for_all_namespaces()


    models_to_start = []
    for job in jobs:
        deployment = next((d for d in deploys.items if d.metadata.name == sanitize_model_name(job.model.image)), None)
        if deployment is None:
            models_to_start.append(job)
            continue
        elif deployment.spec.replicas != job.replicas:
            print(deployment.spec.replicas)
            models_to_start.append(job)
    return models_to_start

def quickstart_model(job: EvalJob, cpu: boolean = False):
    try:
        config.load_incluster_config()

        batch_v1 = client.AppsV1Api()

        # Check for deployment
        deploys = batch_v1.list_deployment_for_all_namespaces()
        print(f'found {len(deploys.items)}')
        deployment = next((d for d in deploys.items if d.metadata.name == sanitize_model_name(job.model.image)), None)
        if deployment:
            print('existing deployment found')
            update_deployment_replicas(deployment, job.replicas, batch_v1)
        else:
            # Create Deployment if it doesn't exist
            print('no existing deployment exists')
            container = create_quickstart_deployment(job, job.model.image, batch_v1)

    except:
        raise

def turn_off_all_models():
    return model_db.stop_all_models()

def update_deployment_replicas(deployment, num, client_instance):
    deployment.spec.replicas = num
    client_instance.patch_namespaced_deployment(deployment.metadata.name, 'default', deployment)

def create_quickstart_deployment(job, image, client_instance):
    print(f'creating deployment for {image}')
    environment = [
        client.V1EnvVar(name='RESULT_QUEUE', value= str(messaging_service.EVAL_QUEUE)),
        client.V1EnvVar(name='QUEUE', value= str(job.model.id)),
        client.V1EnvVar(name='ID', value= str(job.model.id)),
        client.V1EnvVar(name='RABBITMQ_URL', value= settings_service.get_rabbitmq_url()),
    ]

    volume_mounts = [
        client.V1VolumeMount(mount_path='/opt/images', name='medai-ai-images')
    ]
    name = sanitize_model_name(image)
    metadata = client.V1ObjectMeta(
        name = name,
        labels={"app": 'ai'},
        namespace='default'
    )
    container = client.V1Container(
        name=name,
        image=image,
        env=environment,
        volume_mounts=volume_mounts,
        image_pull_policy="Always",
    )

    print('container made')


    print('metadata made')
    volume = client.V1Volume(name = 'medai-ai-images', persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name='medai-ai-images'))

    template = client.V1PodTemplateSpec(
            metadata=metadata,
            spec=client.V1PodSpec(
                containers=[container],
                volumes=[volume]
            ))
    print('template made')

    spec = client.V1DeploymentSpec(
        replicas=job.replicas,
        template=template,
        selector=client.V1LabelSelector(match_labels={"app": 'ai'}),
    )

    deployment_config = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=metadata,
        spec=spec
    )


    return client_instance.create_namespaced_deployment(
        namespace='default',
        body=deployment_config,
        pretty=True
    )