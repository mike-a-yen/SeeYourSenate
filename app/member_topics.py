from app import db, BASE_DIR
from app.models import *
from app.member_utils import member_vote_table
from app.utils import merge_dicts

import os
import pandas as pd
import numpy as np
import re
import json
import pickle

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
    df = member_vote_table(memid)
    print('vote record loaded')
    vectorizer = load_vectorizer(memid)
    print('vectorizer loaded')
    features = vectorizer.get_feature_names()
    votes = ['Nay','Yea']
    print('votes',votes)
    topic_words = {vote:set() for vote in votes}
    print('Start loop')
    for vote in votes:
        sub = df[df['vote']==vote]
        print('got',vote,'votes')
        matrix = vectorizer.fit_transform(sub['body'])
        print('Start KMeans',vote)
        k = len(sub['subject'].unique())
        print(k,'clusters')
        kmeans = KMeans(k)
        kmeans.fit_transform(matrix)
        print('Fit KMeans',vote)
        topic_freq = [get_word_freq_from_centroid(centroid, features, 10)\
                      for centroid in kmeans.cluster_centers_]
        topic_words[vote] = merge_dicts(topic_freq)
    return topic_words

