"""Database queries used by med-ai runner"""

import json
from typing import List, Dict
from services.orthanc_service import OrthancMetadata
from sqlalchemy import or_, and_


from services import logger_service
from db.connection_manager import SessionManager
from db.models import Model, Study, StudyEvaluation

class StudyDB(SessionManager):
    def get_study_by_orthanc_id(self, orthanc_id: str) -> Study:
        """
        Gets a study by orthanc_id
        Args:
            orthanc_id (str): the orthanc_study
        Returns:
            Dict: the default classifier model
        """

        logger_service.log(f'inserting study for orthanc Id: {orthanc_id}')
        study: List[Study] = self.session.query(Study).filter(Study.orthancStudyId==orthanc_id).scalar()
        return study

    def get_studies_for_model(self, model_id: int) ->List[Study]:
        """
        Get studies from db that have not yet been evaluated by a given model

        Args:
            model_id (int): the db id of the model

        Returns:
            List: a list of unevaluated studies
        """
        model:Model = self.session.query(Model).filter(Model.id==model_id).scalar()
        print(model.id)
        studies: List[Study] = self.session.query(Study).\
                                            join(StudyEvaluation, and_(StudyEvaluation.studyId == Study.id, StudyEvaluation.modelId == model.id), isouter=True).\
                                            filter(Study.modality == model.modality).\
                                            filter(StudyEvaluation.id == None)

        studies = studies.all()

        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return studies

    def remove_study_by_id(self, orthanc_id: str):
        """
        Removes a study from the db by its orthanc ID

        Args:
            orthanc_id (str): the study id of the orthanc study
        """
        self.session.query(Study).filter(Study.orthancStudyId == orthanc_id).delete()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

    def remove_orphan_studies(self):
        """
        removes studies that don't have a type
        """
        self.session.query(Study).filter(Study.type == None).delete()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

        print('cleaned orphan studies')

    def get_studies(self) -> List[Study]:
        """
        gets all db studies

        Returns
            List[Dict]: all of the studies in the database
        """

        studies = self.session.query(Study).all()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return studies

    def save_patient_metadata(self, metadata: OrthancMetadata):
        """
        Saves a patient id to the database for a study

        Args:
            metadata (OrthancMetadata): metdata from orthanc
        """

        study = self.session.query(Study).filter(Study.orthancStudyId == metadata.orthanc_id).scalar()
        study.patientId = metadata.patient_id, 
        study.modality = metadata.modality, 
        study.studyUid = metadata.study_uid, 
        study.seriesUid = metadata.series_uid, 
        study.accession = metadata.accession,
        study.description = metadata.description

        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
                                

    def save_study_type(self, orthanc_id: str, study_type: str) -> Dict:
        """
        Saves a study to the database with it accompanying type

        Args:
            orthanc_id (str): the study ID from orthanc
            study_type (str): the type of the study (e.g. Frontal_CXR)

        Returns:
            Dict: the inserted study
        """

        study = self.session.query(Study).filter(Study.orthancStudyId==orthanc_id).scalar()
        study.type = study_type
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise


    def insert_studies(self, orthanc_ids: list) -> Dict:
        """
        Saves a study to the database with it accompanying type

        Args:
            orthanc_id (int): the study ID from orthanc
            study_type (str): the type of the study (e.g. Frontal_CXR)

        Returns:
            Dict: the inserted study as dict
        """
        if len(orthanc_ids) == 0:
            return None
        studies = [Study(orthancStudyId = orthanc_id) for orthanc_id in orthanc_ids]

        self.session.add_all(studies)
        studies = self.session.query(Study).\
                            filter(Study.orthancStudyId.in_(orthanc_ids)).\
                            all()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise

        return studies

    def get_study_by_eval_id(self, eval_id):
        study = self.session.query(Study, StudyEvaluation).\
                    filter(Study.id == StudyEvaluation.studyId).\
                    filter(StudyEvaluation.id==eval_id).scalar()
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return study