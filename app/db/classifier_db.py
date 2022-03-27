"""Database queries used by med-ai runner"""

from db.models import Classifier, Model, Study
from utils.db_utils import DBConn

def get_classifier_model(modality: str) -> Classifier:
    """
    Gets a classifier model for a given modality

    Args:
        modality (str): the modality of the studies

    Returns:
        Dict: the classifer model that pertains to the given modality
    """
    with DBConn() as session:
        classifier = session.query(Classifier).join(Model).\
                                        filter(Model.modality==modality).scalar()
    return classifier


def fail_classifer(study_id: int):
    """
    Updates study evalutation status to failed

    Args:
        eval_id: the db id of the failed evaluation
    """

    with DBConn() as session:
        study = session.query(Study).filter(Study.orthancStudyId==study_id).scalar()
        study.failed = True

