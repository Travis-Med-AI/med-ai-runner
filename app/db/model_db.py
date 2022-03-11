"""Database queries used by med-ai runner"""

import json
from typing import Dict, List
from db.connection_manager import SessionManager
from db.models import Model


class ModelDB(SessionManager):
    def get_model(self, model_id: int) -> Dict:
        """
        selects a single model from the database by id

        Args:
            model_id (int): the database id of the model

        Returns:
            Dict: a dictionary containing the model
        """

        # sql = f'''
        # select * from model
        # where id={model_id}
        # '''

        model = self.session.query(Model).filter(Model.id==model_id).scalar()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return model

    def get_models_to_quickstart(self) -> List[Model]:
        """
        selects all models from database with quickstart enabled that are not currently running

        Returns:
            Dict: a dictionary containing the model
        """    
        
        # sql = '''
        # SELECT * FROM model
        # where running=false and "quickStart"=true
        # '''
        models = self.session.query(Model).\
                            filter(Model.quickStart==True).all()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return models

    def mark_models_as_quickstarted(self, model_ids):
        """
        sets a model as quickstarted

        Args:
            model_ids (List[int]): the models to mark as quick started
        """

        # sql = f'''
        # UPDATE model
        # SET "running"=true
        # WHERE "id" in ({join_for_in_clause(model_ids)})
        # '''

        model = self.session.query(Model).filter(Model.id.in_(model_ids)).scalar()
        model.quickStartRunning = True
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

    def stop_all_models(self):
        """
        sets a model as quickstarted

        Args:
            model_ids (List[int]): the models to mark as quick started
        """

        # sql = f'''
        # UPDATE model
        # SET "running"=false
        # '''

        model = self.session.query(Model)
        model.running = False
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

    def mark_model_as_stopped(self, model_id):
        """
        sets a model as quickstarted

        Args:
            model_ids (List[int]): the models to mark as quick started
        """

        # sql = f'''
        # UPDATE model
        # SET "running"=false
        # WHERE id = {model_id}
        # '''
        model = self.session.query(Model).filter(Model.id==model_id)
        model.quickStartRunning = False
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise