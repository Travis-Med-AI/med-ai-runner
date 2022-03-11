"""Database queries used by med-ai runner"""
from db.connection_manager import SessionManager
from db.models import Experiment, Study, StudyEvaluation

class ExperimentDB(SessionManager):
    def get_studies_for_experiment(self, experiment_id):
        """
        """
        # sql = f'''
        # SELECT  distinct s.* FROM study s
        # LEFT JOIN study_evaluation se on s.id = se."studyId"
        # INNER JOIN experiment_studies_study es on s.id = es."studyId"
        # WHERE se.id is null
        # '''
        experiment_study_ids = [s.id for s in self.session.query(Experiment).filter(Experiment.id == experiment_id).scalar().study]
        
        studies = self.session.query(Study).\
                               filter(Study.id.in_(experiment_study_ids)).\
                               outerjoin(StudyEvaluation).\
                               filter(StudyEvaluation.id == None).distinct().all()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return studies


    def get_running_studies_for_experiment(self, experiment_id):
        """
        """
        # sql = f'''
        # SELECT  distinct s.* FROM study s
        # LEFT JOIN study_evaluation se on s.id = se."studyId"
        # INNER JOIN experiment_studies_study es on s.id = es."studyId"
        # WHERE se.status='RUNNING'
        # '''

        experiment_study_ids = [s.id for s in self.session.query(Experiment).filter(Experiment.id == experiment_id).scalar().study]
        
        studies = self.session.query(Study).\
                               filter(Study.id.in_(experiment_study_ids)).\
                               join(StudyEvaluation).\
                               filter(StudyEvaluation.status == 'RUNNING').distinct().all()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return studies

    def get_running_experiments(self):
        """
        """
        # sql = f'''
        # SELECT * FROM experiment e
        # WHERE e.status = 'RUNNING'
        # '''

        exps = self.session.query(Experiment).\
                            filter(Experiment.status=='RUNNING').all()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return exps

    def set_experiment_complete(self, experiment_id):
        """
        """
        # sql = f'''
        # UPDATE experiment
        # SET "status"='COMPLETED'
        # WHERE id='{experiment_id}'
        # '''
        exp = self.session.query(Experiment).filter(Experiment.id == experiment_id).scalar()
        exp.status = 'COMPLETED'
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

    def set_experiment_failed(self, experiment_id):
        """
        """
        # sql = f'''
        # UPDATE experiment
        # SET "status"='STOPPED'
        # WHERE id='{experiment_id}'
        # '''
        exp = self.session.query(Experiment).filter(Experiment.id == experiment_id).scalar()
        exp.status = 'STOPPED'
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
