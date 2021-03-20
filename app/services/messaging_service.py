"""Utilities for sending rabbitmq messages"""

import pika
from services import logger_service
import json
import traceback
from medaimodels import ModelOutput

def send_message(queue: str, message:str):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))

        channel = connection.channel()
        channel.queue_declare(queue)

        channel.basic_publish(exchange='',
                                routing_key=queue,
                                body=message)
        logger_service.log(f'sent message to {queue}: {message}')
        connection.close()
    except:
        logger_service.log_error(f'Failed sending message to {queue}, message: {message}', traceback.format_exc())


def send_notification(msg: str, notification_type: str):
    """Send notification to the message queue"""
    message = json.dumps({"message": msg, "type": notification_type})
    send_message('notifications', message)


def send_model_log(eval_id: str, line: str):
    message = json.dumps({"evalId": eval_id, "line": line})
    send_message('model_log', message)


def get_result(redis_connection, eval_id: int) -> ModelOutput:
    """
    Retrieve Numpy array from Redis key

    Args:
        redis_connection (:obj): the redis connection
        study_id (int): the ID of the study

    Returns
        :obj:`ModelOutput`: the output received from redis
    """
    output = redis_connection.get(eval_id)
    print('here is the output \n\n\n\n', output)
    return json.loads(output)
