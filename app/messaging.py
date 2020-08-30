"""Utilities for sending rabbitmq messages"""

import pika
import logger
import json
import traceback

def send_message(queue: str, message:str):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))

        channel = connection.channel()
        channel.queue_declare(queue)

        channel.basic_publish(exchange='',
                                routing_key=queue,
                                body=message)
        logger.log(f'sent message to {queue}: {message}')
        connection.close()
    except:
        logger.log_error(f'Failed sending message to {queue}, message: {message}', traceback.format_exc())


def send_notification(msg: str, notification_type: str):
    """Send notification to the message queue"""
    message = json.dumps({"message": msg, "type": notification_type})
    send_message('notifications', message)


def send_model_log(eval_id: str, line: str):
    message = json.dumps({"evalId": eval_id, "line": line})
    send_message('model_log', message)
    
