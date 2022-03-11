from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine 

engine = create_engine('postgresql://test:test@postgres-db:5432/ai')
import db.models as models

Session = sessionmaker(bind=engine)


class SessionManager(object):
    def __init__(self):
        print('opening connection')
        self.session = Session()