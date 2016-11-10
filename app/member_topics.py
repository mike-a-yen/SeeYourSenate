from app import db, BASE_DIR
from app.models import *
from app.build_models import (get_decision_text,
                              get_vote_history,
                              vote_map)
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
    member = db.session.query(Member).filter_by(id=memid).first()
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

def member_vote_table(memid):
    text = get_decision_text(memid)
    df = pd.DataFrame(text,columns=['title','question','subject'])
    df['vote'] = get_vote_history(memid)
    df['body'] = df['title'].str.cat(df['question'],sep=' ')\
                                .str.cat(df['subject'],sep=' ')
    df['body'] = df['body'].apply(lambda x: re.sub("\d+", "", x))
    df['result'] = df['vote'].apply(vote_map)
    return df

def vote_topic_freq(memid):
    df = member_vote_table(memid)
    vectorizer = load_vectorizer(memid)
    features = vectorizer.get_feature_names()
    votes = df['vote'].unique()
    topic_words = {vote:set() for vote in votes}
    for vote in votes:
        sub = df[df['vote']==vote]
        matrix = vectorizer.fit_transform(sub['body'])
        kmeans = KMeans( min(8,len(sub)) )
        kmeans.fit_transform(matrix)
        sub['cluster'] = kmeans.labels_.tolist()
        topic_freq = [get_word_freq_from_centroid(centroid, features, 10)\
                      for centroid in kmeans.cluster_centers_]
        topic_words[vote] = merge_dicts(topic_freq)
    return topic_words
