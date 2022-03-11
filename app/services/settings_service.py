import os
from db.settings_db import SettingsDB

settings_db = SettingsDB()

def get_settings():
    rabbitmq_url = os.getenv('RABBIT_MQ_URL') or 'amqp://guest:guest@rabbitmq:5672'
    redis_url = os.getenv('REDIS_URL') or 'redis://redis:6379'
    orthanc_url = os.getenv('ORTHANC_URL') or 'http://orthanc:8042'
    postgres_url = os.getenv('POSTGRES_URL') or "postgresql://test:test@postgres-db:5432/ai"
    default_settings = {
        'rabbitmqUrl': rabbitmq_url,
        'redisUrl': redis_url,
        'orthancUrl': orthanc_url,
        'postgresUrl': postgres_url
    }
    settings = settings_db.get_settings()
    if not settings:
        settings = default_settings
    else:
        settings['rabbitmqUrl'] = default_settings['rabbitmqUrl'] if not settings['rabbitmqUrl'] else settings['rabbitmqUrl']
        settings['redisUrl'] = default_settings['redisUrl'] if not settings['rabbitmqUrl'] else settings['rabbitmqUrl']
        settings['orthancUrl'] = default_settings['orthancUrl'] if not settings['rabbitmqUrl'] else settings['rabbitmqUrl']
        settings['postgresUrl'] = default_settings['postgresUrl'] if not settings['postgresUrl'] else settings['postgresUrl']
    return settings

def get_redis_url():
    settings = get_settings()
    url = settings['redisUrl']
    return url

def get_rabbitmq_url():
    settings = get_settings()
    url = settings['rabbitmqUrl']
    return url

def get_orthanc_url():
    settings = get_settings()
    url = settings['orthancUrl']
    return url

def get_postgres_url():
    settings = get_settings()
    url = settings['postgresUrl']
    return url