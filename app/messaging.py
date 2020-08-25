"""Utilities for sending rabbitmq messages"""

import pika
import logger


def send_notification(msg):
    """Send notification to the message queue"""
    NOTIFICATION_ROUTE = 'notifications'
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))

    channel = connection.channel()
    channel.queue_declare(NOTIFICATION_ROUTE)
    channel.basic_publish(exchange='', routing_key=NOTIFICATION_ROUTE, body=msg)
    logger.log(f'send message: {msg}')
    connection.close()
