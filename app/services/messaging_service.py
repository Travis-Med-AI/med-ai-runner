"""Utilities for sending rabbitmq messages"""

import pika
from services import logger_service
import json
import traceback
from medaimodels import ModelOutput
import settings

CLASSIFIER_QUEUE = 'classifier_results'
EVAL_QUEUE = 'eval_results'

def send_message(queue: str, message):
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


def start_result_queue():
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))

    channel = connection.channel()
    channel.queue_declare(EVAL_QUEUE)
    channel.queue_declare(CLASSIFIER_QUEUE)


def get_channel():
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()

    return channel
