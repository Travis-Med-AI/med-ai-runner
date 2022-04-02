"""Database queries used by med-ai runner"""
from db.models import Experiment, Study, StudyEvaluation
from utils.db_utils import DBConn

def get_studies_for_experiment(experiment_id):
    """
    """
    # sql = f'''
    # SELECT  distinct s.* FROM study s
    # LEFT JOIN study_evaluation se on s.id = se."studyId"
    # INNER JOIN experiment_studies_study es on s.id = es."studyId"
    # WHERE se.id is null
    # '''
    with DBConn() as session:
        experiment_study_ids = [s.id for s in session.query(Experiment).filter(Experiment.id == experiment_id).scalar().study]
        
        studies = session.query(Study).\
                            filter(Study.id.in_(experiment_study_ids)).\
                            outerjoin(StudyEvaluation).\
                            filter(StudyEvaluation.id == None).distinct().all()

    return studies


def get_running_studies_for_experiment(experiment_id):
    """
    """
    # sql = f'''
    # SELECT  distinct s.* FROM study s
    # LEFT JOIN study_evaluation se on s.id = se."studyId"
    # INNER JOIN experiment_studies_study es on s.id = es."studyId"
    # WHERE se.status='RUNNING'
    # '''

    with DBConn() as session:
        experiment_study_ids = [s.id for s in session.query(Experiment).filter(Experiment.id == experiment_id).scalar().study]
        
        studies = session.query(Study).\
                            filter(Study.id.in_(experiment_study_ids)).\
                            join(StudyEvaluation).\
                            filter(StudyEvaluation.status == 'QUEUED').distinct().all()

    return studies

def get_running_experiments():
    """
    """
    # sql = f'''
    # SELECT * FROM experiment e
    # WHERE e.status = 'RUNNING'
    # '''

    with DBConn() as session:
        exps = session.query(Experiment).\
                            filter(Experiment.status=='RUNNING').all()

    return exps

def set_experiment_complete(experiment_id):
    """
    """
    # sql = f'''
    # UPDATE experiment
    # SET "status"='COMPLETED'
    # WHERE id='{experiment_id}'
    # '''
    with DBConn() as session:
        exp = session.query(Experiment).filter(Experiment.id == experiment_id).scalar()
        exp.status = 'COMPLETED'


def set_experiment_failed(experiment_id):
    """
    """
    # sql = f'''
    # UPDATE experiment
    # SET "status"='STOPPED'
    # WHERE id='{experiment_id}'
    # '''
    with DBConn() as session:
        exp = session.query(Experiment).filter(Experiment.id == experiment_id).scalar()
        exp.status = 'STOPPED'

