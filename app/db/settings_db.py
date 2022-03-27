"""Database queries used by med-ai runner"""

from db.models import AppSetting
from utils.db_utils import DBConn

def get_settings() -> AppSetting:
    with DBConn() as session:
        settings = session.query(AppSetting).scalar()

    return settings
