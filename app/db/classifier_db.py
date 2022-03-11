"""Database queries used by med-ai runner"""

from db.connection_manager import SessionManager
from db.models import Classifier, Model, Study

class ClassiferDB(SessionManager):
    def get_classifier_model(self, modality: str) -> Classifier:
        """
        Gets a classifier model for a given modality

        Args:
            modality (str): the modality of the studies

        Returns:
            Dict: the classifer model that pertains to the given modality
        """
        classifier = self.session.query(Classifier).join(Model).\
                                            filter(Model.modality==modality).scalar()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return classifier


    def fail_classifer(self, study_id: int):
        """
        Updates study evalutation status to failed

        Args:
            eval_id: the db id of the failed evaluation
        """

        study = self.session.query(Study).filter(Study.orthancStudyId==study_id).scalar()
        study.failed = True
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

