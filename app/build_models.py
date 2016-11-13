from app import BASE_DIR

from app import db
from app.models import *
from app.member_utils import (member_vote_table,
                              member_vote_subject_table,
                              get_bill_subject,
                              vote_map)
from app.utils import (get_member)


import pandas as pd
import numpy as np
import re
import json
import pickle
from multiprocessing import Pool, cpu_count

from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

import nltk
nltk.data.path.append(BASE_DIR+'/nltk_data/')
from nltk.stem.snowball import SnowballStemmer
from textblob import TextBlob
stemmer = SnowballStemmer('english')

stopwords = nltk.corpus.stopwords.words('english')
stopwords += ['amdt', 'amend', 'amendment',
              'bill', 'motion','title','act','samdt',
              'table','year','cba','pn','con','sec',
              'fy','use','used','uses']


def tokenize_and_stem(text, stopwords=stopwords):
    tokens = [word for word in TextBlob(text).words]
    filtered_tokens = [re.sub('[^a-zA-Z]','',w) for w in tokens]
    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems

def build_model(memid):
    """Build a knn model for each member
    member is a database Member object
    """
    df = member_vote_table(memid)
    
    tfidf = TfidfVectorizer(max_features=1000,
                            stop_words=stopwords,
                            use_idf=True,
                            tokenizer=None,
                            ngram_range=(1,3))

    tfidf_matrix = tfidf.fit_transform(df['body'])
    clf =  KNeighborsClassifier(n_neighbors=50,
                                weights='distance')
    clf.fit(tfidf_matrix,df['result'].values)
    return clf, tfidf


def build_save_model(member):
    print(member.first_name, member.last_name)
    memid = member.member_id
    member.nn_model_path = 'data/nn_models/'+memid+'.pklb'
    member.vectorizer_path = 'data/vectorizers/'+memid+'.pklb'
    db.session.commit()
    clf, tfidf = build_model(memid)
    
    pickle.dump(clf,open(member.nn_model_path,'wb'))
    pickle.dump(tfidf,open(member.vectorizer_path,'wb'))
    return True
    
def build_models():
    """Build knn models for all members in DB
    this can be run whenever the db gets an update
    """
    members = db.session.query(Member).all()
    p = Pool(4)
    results = p.map(build_save_model,members)
    return np.mean(results) == 1

def get_subject_votes(memid):
    
    df = pd.DataFrame(list(zip(subjects,votes)), columns=['subject','vote'])
    return df

def rank_subjects(memid):
    df = member_vote_subject_table(memid)
    df = df[df['vote'].isin(['Nay','Yea'])]
    df['value'] = df['vote'].apply(vote_map)
    group = df.groupby(['subject'],as_index=False)
    agg = group.agg(['mean','count'])['value']\
               .sort_values(['mean','count'],ascending=False)
    agg['for_vote'] = (agg['mean']*agg['count']).astype(int)
    agg['against_vote'] = agg['count']-agg['for_vote']
    agg = agg.round({'mean':2})
    return agg.reset_index(0)

def positive_negative_subjects(memid,wiggle_room=0.5,limit=5):
    ranked = rank_subjects(memid)
    positive = ranked[ranked['mean']>=1-wiggle_room].sort_values(['mean','for_vote'],ascending=False)
    negative = ranked[ranked['mean']<=wiggle_room].sort_values(['mean','against_vote'],ascending=[True,False])
    positive_counts = positive[['subject','for_vote']].iloc[0:limit]
    positive_counts.columns=['subject','count']
    negative_counts = negative[['subject','against_vote']].iloc[0:limit]
    negative_counts.columns=['subject','count']
    return (positive_counts.T.to_dict().values(),
            negative_counts.T.to_dict().values())

if __name__ == '__main__':
    build_models()
