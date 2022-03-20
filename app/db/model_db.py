"""Database queries used by med-ai runner"""

import json
from typing import Dict, List
from db.connection_manager import SessionManager
from db.models import EvalJob, Model


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

    def get_jobs_to_quickstart(self) -> List[Model]:
        """
        selects all models from database with quickstart enabled that are not currently running

        Returns:
            Dict: a dictionary containing the model
        """    
        
        # sql = '''
        # SELECT * FROM model
        # where running=false and "quickStart"=true
        # '''
        jobs = self.session.query(EvalJob).all()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return jobs

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
        
    def get_job_by_model(self, model_id: int):
        job = self.session.query(EvalJob).filter(EvalJob.modelId==model_id).scalar()
        return job

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
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise