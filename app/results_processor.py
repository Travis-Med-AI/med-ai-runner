import json
from services import logger_service, classifier_service, eval_service, experiment_service, messaging_service, model_service, orthanc_service, study_service
import json

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
    # write result to db
    eval_service.write_eval_results(result, eval_id)

    # send notification to frontend
    messaging_service.send_notification(f'Finished evaluation {eval_id}', 'new_result')

if __name__  == "__main__":
    print('starting results watcher')
    channel = messaging_service.get_channel()
    channel.queue_declare(messaging_service.EVAL_QUEUE)
    channel.queue_declare(messaging_service.CLASSIFIER_QUEUE)

    channel.basic_consume(queue=messaging_service.CLASSIFIER_QUEUE, 
                          on_message_callback=on_classifier_result, 
                          auto_ack=True)
    channel.basic_consume(queue=messaging_service.EVAL_QUEUE, 
                          on_message_callback=on_eval_result, 
                          auto_ack=True)
    channel.start_consuming()