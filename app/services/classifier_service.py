import traceback
from typing import List

from db.classifier_db import ClassiferDB
from db.eval_db import EvalDB
from db.study_db import StudyDB
from services import messaging_service, logger_service, orthanc_service

study_db = StudyDB()
eval_db = EvalDB()
classifier_db = ClassiferDB()

def classify_studies(study_metadata: List[orthanc_service.OrthancMetadata]) -> None:
    """
    Takes in a list of tuples containing (modality, study_paths) and will use that modality
    classifier to determine the study type.
    """
    # TODO: seems like a lot of nested loops here...revisit and optimize
    for metadata in study_metadata:
        study_db.save_study_type(metadata.orthanc_id, metadata.modality)
        messaging_service.send_notification(f'Study {metadata.orthanc_id} ready', 'study_ready')

        # TODO: implement study classification
        # # evaluate the study using classifier model
        # classifier_model = classifier_db.get_classifier_model(modality)

        # # check to see if there is currently a classifier set for the given modality
        # # if not just get the default one from the db
        # if classifier_model is None:
        #     classifier_model = eval_db.get_default_model()

        # # run studies through the classifier model
        # eval_service.evaluate(classifier_model, study_paths, str(uuid.uuid4()))

    
def fail_classification(orthanc_ids):
        # catch errors and print output
    print('classification of study', orthanc_ids, 'failed')
    traceback.print_exc()
    logger_service.log_error(f'classfying {orthanc_ids} failed', traceback.format_exc())
    # remove studies from the db that failed on classfication
    for orthanc_id in orthanc_ids:
        study_db.remove_study_by_id(orthanc_id)

def save_classification(orthanc_id, result):
    study_db.save_study_type(orthanc_id, result['display'])