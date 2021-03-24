import traceback
import os
import uuid

from db import study_db, eval_db, classifier_db
from services import messaging_service, eval_service, logger_service, orthanc_service

def check_for_ct(orthanc_id: str) -> bool:
    """
    Checks to see if a study from orthanc is a CT scan or not
    by seeing if there are multiple slices in the dicomdir

    Args:
        orthanc_id (str): the study id of the study from orthanc
    Returns:
        :bool: a boolean of whether or not it is a CT scan
    """
    # Check to see if the dicomdir has multiple images
    path = f'/tmp/{orthanc_id}'
    return len(os.listdir(path)) > 1

def classify_studies(studies):
    # TODO: seems like a lot of nested loops here...revisit and optimize
    for modality, study_paths in studies.items():


        # Check to see if the case is a CT scan by seeing if the dicom modality is 'CT'
        # or the DICOMDIR has multiple slices
        # TODO: come up with a better solution for identifying CT scans
        
        if modality == 'CT':
            for orthanc_id in study_paths:
                study_db.save_study_type(orthanc_id, 'CT')
                messaging_service.send_notification(f'Study {orthanc_id} ready', 'study_ready')
            continue

        # evaluate the study using classifier model
        classifier_model = classifier_db.get_classifier_model(modality)

        # check to see if there is currently a classifier set for the given modality
        # if not just get the default one from the db
        if classifier_model is None:
            classifier_model = eval_db.get_default_model()

        # run studies through the classifier model
        results = eval_service.evaluate(classifier_model['image'], study_paths, str(uuid.uuid4()))

        # save the results of classifcation to the database
        # TODO: optimize with BULK insert
        for orthanc_id, result in zip(study_paths, results):
            study_db.save_study_type(orthanc_id, result['display'])
            messaging_service.send_notification(f'Study {orthanc_id} ready', 'study_ready')
    

def fail_classification(orthanc_ids):
        # catch errors and print output
    print('classification of study', orthanc_ids, 'failed')
    traceback.print_exc()
    logger_service.log_error(f'classfying {orthanc_ids} failed', traceback.format_exc())
    # remove studies from the db that failed on classfication
    for orthanc_id in orthanc_ids:
        study_db.remove_study_by_id(orthanc_id)