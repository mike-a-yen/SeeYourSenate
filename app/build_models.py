from app import BASE_DIR

from app import db
from app.models import *
from app.member_utils import (member_vote_table,
                              member_vote_subject_table,
                              get_bill_top_subject,
                              vote_map,FeatureSelector)
from app.utils import (get_member)

import os
import pandas as pd
import numpy as np
import re
import json
import pickle
from multiprocessing import Pool, cpu_count
from functools import partial

from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_extraction.text import TfidfVectorizer,CountVectorizer
from sklearn.pipeline import Pipeline,FeatureUnion


import nltk
nltk.data.path.append(BASE_DIR+'/nltk_data/')
from nltk.stem.snowball import SnowballStemmer
from textblob import TextBlob
stemmer = SnowballStemmer('english')

stopwords = nltk.corpus.stopwords.words('english')
stopwords += ['amdt', 'amend', 'amendment',
              'bill', 'motion','title','act','samdt',
              'table','year','cba','pn','con','sec',
              'fy','use','used','uses','federal','government',
              'america']


def tokenize_and_stem(text, stopwords=stopwords):
    tokens = [word for word in TextBlob(text).words]
    filtered_tokens = [re.sub('[^a-zA-Z]','',w) for w in tokens]
    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems

title_vec = CountVectorizer(max_features=200,
                            ngram_range=(1,2),
                            tokenizer=tokenize_and_stem,
                            stop_words=stopwords)
sub_vec = CountVectorizer(max_features=50,
                          ngram_range=(1,2),
                          tokenizer=tokenize_and_stem,
                          stop_words=stopwords)
text_vec = TfidfVectorizer(max_features=1000,
                           max_df=0.95,
                           min_df=0.05,
                           ngram_range=(1,3),
                           tokenizer=tokenize_and_stem,
                           stop_words=stopwords)

title_features = Pipeline([('selector',FeatureSelector('title')),('count',title_vec)])
subject_features = Pipeline([('selector',FeatureSelector('subject')),('count',sub_vec)])
text_features = Pipeline([('selector',FeatureSelector('text')),('tfidf',text_vec)])

class DataPipeline(FeatureUnion):
    def __init__(self,**kwargs):
        FeatureUnion.__init__(self,
                              transformer_list=[('title',title_features),
						('subject',subject_features),
						('text',text_features)],
				**kwargs)

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
    clf =  KNeighborsClassifier(n_neighbors=10,
                                weights='distance')
    clf.fit(tfidf_matrix,df['result'].values)
    return clf, tfidf


def build_save_model(member,version):
    print(member.first_name, member.last_name)
    memid = member.member_id
    
    if not os.path.exists('data/nn_models/v%s'%version):
        os.mkdir('data/nn_models/v%s'%version)
    if not os.path.exists('data/vectorizers/v%s'%version):
        os.mkdir('data/vectorizers/v%s'%version)
    member.nn_model_path = 'data/nn_models/v%s/%s.pklb'%(version,memid)
    member.vectorizer_path = 'data/vectorizers/v%s/%s.pklb'%(version,memid)

    clf, tfidf = build_model(memid)
    algorithm = re.search('([a-zA-Z0-9]+)',clf.__repr__()).group()
    db_model = PredictionModel(memid,
                               member.nn_model_path,
                               algorithm,
                               version)
    db.session.add(db_model)
    db.session.commit()
    
    pickle.dump(clf,open(member.nn_model_path,'wb'))
    pickle.dump(tfidf,open(member.vectorizer_path,'wb'))
    return True
    
def build_models(version,members=None):
    """Build knn models for all members in DB
    this can be run whenever the db gets an update
    """
    if members == None:
        members = db.session.query(Member).all()
    p = Pool(1)

    partial_save_model = partial(build_save_model, version=version)
    
    results = p.map(partial_save_model,members)
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
    positive_counts = positive[['subject','for_vote','count']].iloc[0:limit]
    positive_counts.columns=['subject','for_votes','total_votes']
    negative_counts = negative[['subject','against_vote','count']].iloc[0:limit]
    negative_counts.columns=['subject','against_votes','total_votes']
    return (positive_counts.T.to_dict().values(),
            negative_counts.T.to_dict().values())

def voting_subject_record(memid):
    ranked = rank_subjects(memid)
    return ranked.T.to_dict().values()


if __name__ == '__main__':
    build_models()
