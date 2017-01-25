from app import BASE_DIR

from app import db
from app.models import *
from app.member_utils import (member_vote_table,
                              member_vote_subject_table,
                              get_bill_top_subject,
                              vote_map)
from app.utils import (get_member)


import numpy as np
from datetime import datetime
from sqlalchemy import func, desc
from sklearn.externals import joblib



def senator_prediction(member,version,bill_data):
    model_query = db.session.query(PredictionModel)\
                            .filter_by(member_id=member.member_id)\
                            .filter_by(version=version)
    prediction_model = model_query.first()
    if prediction_model:
        model = joblib.load(prediction_model.model_path)
        return model.predict(bill_data)
    else:
        return np.array([None])

def senate_prediction(members,bill_data):
    predictions = np.vstack((senator_prediction(member,bill_data) for member in members))
    return prediction
