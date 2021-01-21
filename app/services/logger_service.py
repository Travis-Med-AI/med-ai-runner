"""Logstash logger for runnner"""

# import logging
# import logstash
# from typing import Dict

# HOST = 'logstash'

# logger = logging.getLogger('python-logstash-logger')
# logger.setLevel(logging.INFO)
# logger.addHandler(logstash.LogstashHandler(HOST, 5000, version=1))

# test_logger.addHandler(logstash.TCPLogstashHandler(host, 5959, version=1))
def log(message: str, extras: Dict = None):
    """
    Logs a message to logstash
    
    Args:
        message (str): the message to log
    """
    # logger.info(message, extra=extras)


def log_error(message, stack):
    """
    Logs an error to logstash

    Args:
        message (str): the message to log
    """
    extra = {
        'stack': stack
    }
    # try:
    #     # logger.error(message, extra=extra)
    # except:
    #     print('failed logging', message)