from typing import List
from collections import defaultdict
from db import study_db

from services import orthanc_service


def get_studies_for_model(model_id: int, batch_size: int):
    studies = study_db.get_studies_for_model(model_id)
    # trim studies down to batch size
    studies = studies[:batch_size]
    return studies

def get_new_studies(batch_size: int) -> list[str]:
    """
    takes in a batch size and returns the same number of orthanc ids that have not yet 
    been downloaded to the db
    """
    # get orthanc study ids from orthanc
    orthanc_studies = orthanc_service.get_orthanc_study_ids()

    # get ids of studies that have already been processed and saved to the db
    db_orthanc_ids = map(lambda x: x.orthancStudyId, study_db.get_studies())

    # filter out studies that have already been evaluated
    # TODO: this should be done with a db call the dose WHERE NOT IN ()
    filtered_studies = list(set(orthanc_studies) - set(db_orthanc_ids))
    filtered_studies = filtered_studies[:batch_size]

    study_db.insert_studies(filtered_studies)

    return filtered_studies

def save_study_metadata(orthanc_ids: List[str]) -> List[orthanc_service.OrthancMetadata]:
    # download metadata for all studies
    all_metadata = [orthanc_service.get_study_metadata(orthanc_id) for orthanc_id in orthanc_ids]
    # save metadata to db 
    [study_db.save_patient_metadata(metadata) for metadata in all_metadata]
    return all_metadata

def refresh_orthanc_data():
    studies = study_db.get_studies()
    print('updating studies')
    for study in studies:
        orthanc_id = study.orthancStudyId
        # download study from orthanc to disk
        metadata = orthanc_service.get_study_metadata(orthanc_id)
        # save the patient id
        study_db.save_patient_metadata(metadata)

def remove_orphan_studies():
    study_db.remove_orphan_studies()

def get_study_by_eval_id(eval_id):
    return study_db.get_study_by_eval_id(eval_id)

def get_old_studies(time: int)->List[str]:
    return study_db.get_old_studies(time)