from app import app,db
from app.models import *

import pandas as pd
import numpy as np
import re

from sklearn.base import BaseEstimator,TransformerMixin

def vote_map(vote, default=0):
    if vote == 'Yea':
        return 1
    elif vote == 'Nay':
        return 0
    else:
        return default

def get_bills_by_member_id(memid):
    bills = db.session.query(Bill)\
                      .filter(Session.session_id==MemberSession.session_id)\
                      .filter(MemberSession.member_id==memid)\
                      .filter(Session.bill_id==Bill.bill_id).all()
    return bills

def get_bill_title(memid):
    bills = get_bills_by_member_id(memid)
    return list(map(lambda x: x.title if x.title != None else '', bills))

def get_bill_top_subject(memid):
    bills = get_bills_by_member_id(memid)
    return list(map(lambda x: x.top_subject if x.top_subject != None else '', bills))

def get_bill_subjects(bill_id):
    subjects = db.session.query(BillSubject.subject)\
               .filter_by(bill_id=bill_id).all()
    return [x[0] for x in subjects]

def get_vote_history(memid):
        votes = db.session.query(MemberSession.vote)\
                .filter_by(member_id=memid).all()
        return list(map(lambda x: x[0],votes))

    
def member_vote_table(memid):
    vote_query = db.session.query(Bill.bill_id,
                                  Bill.title,
                                  Bill.top_subject,
                                  Bill.text,
                                  Session.date,
                                  MemberSession.vote)\
                           .filter(MemberSession.session_id==Session.session_id)\
                           .filter(Session.bill_id==Bill.bill_id)\
                           .filter(MemberSession.member_id==memid)

    df = pd.DataFrame(vote_query.all())
    #df['subjects'] = df['bill_id'].apply(get_bill_subjects)
    df['vote'] = df['vote'].apply(vote_map)
    return df

def member_vote_subject_table(memid):
    query = db.session.query(Bill.top_subject,MemberSession.vote)\
                      .filter(Bill.bill_id==Session.bill_id)\
                      .filter(Session.session_id==MemberSession.session_id)\
                      .filter(MemberSession.member_id==memid).all()
    df = pd.DataFrame(query,columns=['subject','vote'])
    df['result'] = df['vote'].apply(vote_map)
    return df
