"""Database queries used by med-ai runner"""

from db.connection_manager import SessionManager
from db.models import AppSetting


class SettingsDB(SessionManager):
    def get_settings(self) -> AppSetting:
        sql = f'''
        select * from app_settings
        '''

        settings = self.session.query(AppSetting).scalar()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return settings
