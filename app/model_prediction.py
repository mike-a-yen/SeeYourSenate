from app import app, db, BASE_DIR
from app.utils import get_senate

import os
import numpy as np
import pickle
from multiprocessing import Pool, cpu_count
from functools import partial

def senate_prediction(members, bills):
    """bills is a list of bill objects"""
    predict_func = partial(member_prediction,bills=bills)
    p = Pool(cpu_count())
    results = p.map(predict_func,members)
    votes = np.vstack(results)
    return votes
        

def member_prediction(member,bills):
    """predct member's vote on bills
    bills is an iterable of bill objects
    """
    vectorizer = pickle.load(open(os.path.join(BASE_DIR,
                                               member.vectorizer_path),
                                  'rb'))
    model = pickle.load(open(os.path.join(BASE_DIR,
                                          member.nn_model_path),
                             'rb'))

    text = data_pipeline(bills)
    tfidf_vec = vectorizer.transform(text)
    prediction = model.predict(tfidf_vec)
    return prediction

def data_pipeline(bills):
    """bills is a list of bill objects"""
    for bill in bills:
        text = bill.title+' '+\
               bill.top_subject+' '+\
               bill.text
        yield text

    
