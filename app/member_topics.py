from app import app,db, BASE_DIR
from app.models import *
from app.member_utils import member_vote_table
from app.utils import merge_dicts

import os
import pandas as pd
import numpy as np
import re
import json
import pickle

from sqlalchemy import func

from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer



def load_vectorizer(memid):
    member = db.session.query(Member).filter_by(member_id=memid).first()
    path = os.path.join(BASE_DIR,member.vectorizer_path)
    return pickle.load(open(path,'rb'))

def extract_words_from_clusters(features, centroids, n_words=6):
    num_centroids = len(centroids)
    order_centroids = np.argsort(centroids)[:,::-1]

    topics = set()
    for i in range(num_centroids):
        words = [[features[ind]] for ind in order_centroids[i,:n_words]]
        topics = topics.union(*map(set,words))
    return topics

def get_word_freq_from_centroid(centroid, features, n):
    """Given the centroid and features return the
    top n words with their tfidf
    """
    ordered_centroid = centroid.argsort()[::-1]
    word_freq = {features[ind]:centroid[ind] \
                 for ind in ordered_centroid[:n]}
    return word_freq

def vote_topic_freq(memid):
    query = db.session.query(BillSubject.subject,MemberSession.vote, func.count())\
                      .filter(Bill.bill_id==BillSubject.bill_id)\
                      .filter(Session.bill_id==Bill.bill_id)\
                      .filter(Session.session_id==MemberSession.session_id)\
                      .filter(MemberSession.member_id==memid)\
                      .group_by(BillSubject.subject,MemberSession.vote)
    df = pd.read_sql(query.statement,app.config['SQLALCHEMY_DATABASE_URI'])
    print('Query done')
    votes = ['Yea','Nay']
    df = df[df['vote'].isin(votes)]
    groups = df.groupby(['vote','subject'],as_index=False).sum()
    yay = groups[groups['vote']=='Yea']
    nay = groups[groups['vote']=='Nay']
    vote_words = {'Yea':yay['subject'].str.cat(sep=' '),
                  'Nay':nay['subject'].str.cat(sep=' ')}
    return vote_words

