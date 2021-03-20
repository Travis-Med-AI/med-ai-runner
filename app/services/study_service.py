from db import study_db, eval_db
from collections import defaultdict
from services import orthanc_service
import time

def get_studies_for_model(model_id: int, batch_size: int):
    studies = study_db.get_studies_for_model(model_id)
    # trim studies down to batch size
    studies = studies[:batch_size]
    return studies

def get_new_studies(batch_size):
    # get orthanc study ids from orthanc
    orthanc_studies = orthanc_service.get_orthanc_studies()
    

    # get ids of studies that have already been processed and saved to the db
    db_orthanc_ids = map(lambda x: x['orthancStudyId'], study_db.get_studies())

    # filter out studies that have already been evaluated
    # TODO: this should be done with a db call the dose WHERE NOT IN ()
    filtered_studies = list(set(orthanc_studies) - set(db_orthanc_ids))
    filtered_studies = filtered_studies[:batch_size]

    study_db.insert_studies(filtered_studies)

    return filtered_studies

def get_study_modalities(orthanc_ids, modalities):
    studies = defaultdict(list)

    for orthanc_id, modality in zip(orthanc_ids, modalities):
        t0 = time.time()
        # download study from orthanc to disk
        study_path, patient_id, modality, study_uid = orthanc_service.get_study(orthanc_id)
        t1 = time.time()
        print('getting study took', t1-t0)
        # save the patient id
        study_db.save_patient_id(patient_id, orthanc_id, modality, study_uid)

        # add studies to modality dictionary
        studies[modality].append(study_path)
    
    return studies

def remove_orphan_studies():
    study_db.remove_orphan_studies()
