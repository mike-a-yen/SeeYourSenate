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



def senator_prediction(member,version,bill_data,record=False):
    model_query = db.session.query(PredictionModel)\
                            .filter_by(member_id=member.member_id)\
                            .filter_by(version=version)
    prediction_model = model_query.first()
    if prediction_model:
        model = joblib.load(prediction_model.model_path)
        vote =  model.predict(bill_data)[0]
    else:
        vote = None
    if record:
        bill_id = bill_data['bill_id'].iloc[0]
        memid = member.member_id
        model_id = prediction_model.model_id
        vote_prediction = VotePrediction(bill_id, memid, vote,
                                         model_id, datetime.now(),
                                         correct=None)
        return vote_prediction
        db.session.add(vote_prediction)
        db.session.commit()
    return vote

def senate_prediction(members,bill_data,record=False):
    predictions = np.zeros(len(members))
    for i,member in enumerate(members):
        vote = senator_prediction(member,bill_data,record=record)
        predictions[i] = vote
    return prediction

def record_prediction(member,bill_id,vote,model):
    vote_prediction = VotePrediction(bill_id,
                                     member.member_id,
                                     vote,
                                     model.model_id,
                                     datetime.now(),
                                     correct=None)
    
    db.session.add(vote_prediction)
    db.session.commit()
