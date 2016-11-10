from app import BASE_DIR

from app import db
from app.models import *

import pandas as pd
import numpy as np
import re
import json
import pickle

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
              'table','year','cba','pn','con']


def tokenize_and_stem(text, stopwords=stopwords):
    tokens = [word for word in TextBlob(text).words]
    filtered_tokens = [re.sub('[^a-zA-Z]','',w) for w in tokens]
    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems

def error_rate(predictions, actuals):
    return np.mean(predictions != actuals)

def document_title(doc):
    if doc == 'null' or (type(doc)==float and np.isnan(doc)):
        return ''
    else:
        return json.loads(doc).get('title','')
    
def error_rate(predictions, actuals):
    return np.mean(predictions != actuals)


def get_bill_text(memid):
    bills = db.session.query(Bill)\
                      .filter(Session.id==MemberSession.session_id)\
                      .filter(MemberSession.member_id==memid)\
                      .filter(Session.bill_id==Bill.id).all()
    return list(map(lambda x: x.title if x.title != None else '', bills))


def get_session_question(memid):
    sessions = db.session.query(Session.question)\
                         .filter(Session.id==MemberSession.session_id)\
                         .filter(MemberSession.member_id==memid).all()
    questions = list(map(lambda x: x[0],sessions))
    return questions


def get_session_subject(memid):
    sessions = db.session.query(Session.subject)\
                         .filter(Session.id==MemberSession.session_id)\
                         .filter(MemberSession.member_id==memid).all()
    subjects = list(map(lambda x: x[0],sessions))
    return subjects


def get_decision_text(memid):
    bill = get_bill_text(memid)
    question = get_session_question(memid)
    subject = get_session_subject(memid)
    assert len(bill)==len(question)
    assert len(question)==len(subject)
    return list(zip(bill, question, subject))


def get_vote_history(memid):
        votes = db.session.query(MemberSession.vote)\
                .filter_by(member_id=memid).all()
        return list(map(lambda x: x[0],votes))

def vote_map(vote, default=0):
    if vote == 'Yea':
        return 1
    elif vote == 'Nay':
        return 0
    else:
        return default
            
def build_model(memid):
    """Build a knn model for each member
    member is a database Member object
    """
    df = pd.DataFrame(get_decision_text(memid),columns=['title','question','subject'])
    df['vote'] = get_vote_history(memid)
    df['body'] = df['title'].str.cat(df['question'],sep=' ').str.cat(df['subject'],sep=' ')
    df['body'] = df['body'].apply(lambda x: re.sub("\d+", "", x))
    df['result'] = df['vote'].apply(vote_map)
    
    tfidf = TfidfVectorizer(max_features=10000,
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
    memid = member.id
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
    results = [build_save_model(member) for member in members]
    return np.mean(results) == 1
