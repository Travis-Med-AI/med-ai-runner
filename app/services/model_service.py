from db import model_db


def get_model(model_id):
    return model_db.get_model(model_id)
