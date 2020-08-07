import logging
import logstash
import sys

host = 'logstash'

logger = logging.getLogger('python-logstash-logger')
logger.setLevel(logging.INFO)
logger.addHandler(logstash.LogstashHandler(host, 5000, version=1))

# test_logger.addHandler(logstash.TCPLogstashHandler(host, 5959, version=1))
def log(message):
    logger.info(message)

def logError(message):
    logger.error(message)