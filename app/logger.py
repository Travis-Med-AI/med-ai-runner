"""Logstash logger for runnner"""

import logging
import logstash

HOST = 'logstash'

logger = logging.getLogger('python-logstash-logger')
logger.setLevel(logging.INFO)
logger.addHandler(logstash.LogstashHandler(HOST, 5000, version=1))

# test_logger.addHandler(logstash.TCPLogstashHandler(host, 5959, version=1))
def log(message: str):
    """
    Logs a message to logstash

    Args:
        message (str): the message to log
    """
    logger.info(message)


def log_error(message):
    """
    Logs an error to logstash

    Args:
        message (str): the message to log
    """
    logger.error(message)
