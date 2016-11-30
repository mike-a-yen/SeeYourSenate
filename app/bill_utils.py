from app import app,db
from app.models import *

threshold_map = {'1/2':1/2,
                 '3/5':3/5,
                 '2/3':2/3}

def passed(votes_for,votes_against,threshold='1/2'):
    """votes_for / total_votes > threshold 
    threshold is a string '1/2', '3/5', '2/3'
    """
    total = votes_for+votes_against
    return votes_for/total > threshold_map[threshold]


    
