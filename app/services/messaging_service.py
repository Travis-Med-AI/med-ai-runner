"""Utilities for sending rabbitmq messages"""

from db.models import User
from utils.db_utils import RabbitConn
import pika
from services import logger_service
import json
import traceback
from medaimodels import ModelOutput
import services
import json

CLASSIFIER_QUEUE = 'classifier_results'
EVAL_QUEUE = 'eval_results'
LOG_QUEUE = 'log_results'

def send_message(queue: str, message, user_id: int=-1):
    try:
        with RabbitConn() as channel:
            msg_json = json.loads(message)
            channel.queue_declare(queue)
            msg_json['userId'] = user_id
            message = json.dumps(msg_json)

            channel.basic_publish(exchange='',
                                    routing_key=queue,
                                    body=message)
            print(f'sent message to {queue}: {message}')
    except:
        print(f'Failed sending message to {queue}, message: {message}', traceback.format_exc())


def send_notification(msg: str, notification_type: str, user_id: int):
    """Send notification to the message queue"""
    message = json.dumps({"message": msg, "type": notification_type})
    send_message('notifications', message, user_id)


def send_model_log(eval_id: str, line: str):
    message = json.dumps({"evalId": eval_id, "line": line})
    send_message('model_log', message)


def start_result_queue():
    with RabbitConn() as channel:
        channel.queue_declare(EVAL_QUEUE)
        channel.queue_declare(CLASSIFIER_QUEUE)
