from app import db
from app.models import *
import numpy as np
import json
import re
from textblob import TextBlob
from nltk.stem.snowball import SnowballStemmer
stemmer = SnowballStemmer('english')


def tokenize_and_stem(text):
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


def get_random_member():
    n_members = db.session.query(Member).count()
    ind = np.random.randint(0,n_members)
    member = db.session.query(Member).offset(ind).first()
    return member

def merge_dicts(list_of_dicts):
    new = {}
    for d in list_of_dicts:
        new.update(d)
    return new
    
