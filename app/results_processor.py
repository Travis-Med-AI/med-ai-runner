import json
from services import logger_service, classifier_service, eval_service, experiment_service, messaging_service, model_service, orthanc_service, study_service
import json
import traceback

def on_classifier_result(ch, method, properties, body):
    print(f'received classifier result {body}')
    message = json.loads(body)
    orthanc_id = message['id']
    result = message['output']
    classifier_service.save_classification(orthanc_id, result)

    messaging_service.send_notification(f'Study {orthanc_id} ready', 'new_result')

def on_eval_result(ch, method, properties, body):
    print(f'received eval result {body}')


    message = json.loads(body)
    eval_id = message['id']
    result = message['output']
    type = message['type']

    if type == 'FAIL':
        eval_service.fail_dicom_eval(eval_id)
    # write result to db
    eval_service.write_eval_results(result, eval_id)

    study = study_service.get_study_by_eval_id(eval_id)
    # orthanc_service.delete_study_dicom(study['orthancStudyId'])
    # send notification to frontend
    messaging_service.send_notification(f'Finished evaluation {eval_id}', 'new_result')

def on_eval_log(ch, method, properties, body):
    try:
        print(f'received eval log {body}')
        message = json.loads(body)
        eval_id = message['id']
        result = message['output'].split('\n')
        type = message['type']
        print(result)
        eval_service.add_stdout_to_eval([eval_id], result)
    except:
        print('failed to log', body)
        traceback.print_stack()

if __name__  == "__main__":
    print('starting results watcher')
    channel = messaging_service.get_channel()
    channel.queue_declare(messaging_service.EVAL_QUEUE)
    channel.queue_declare(messaging_service.CLASSIFIER_QUEUE)
    channel.queue_declare(messaging_service.LOG_QUEUE)

    channel.basic_consume(queue=messaging_service.CLASSIFIER_QUEUE, 
                          on_message_callback=on_classifier_result, 
                          auto_ack=True)
    channel.basic_consume(queue=messaging_service.EVAL_QUEUE, 
                          on_message_callback=on_eval_result, 
                          auto_ack=True)
    channel.basic_consume(queue=messaging_service.LOG_QUEUE, 
                          on_message_callback=on_eval_log, 
                          auto_ack=True)
    channel.start_consuming()