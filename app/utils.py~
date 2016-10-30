import json
from . import login_manager
from .models import User, Review, Business
from app import db

def load_json(fname):
    with open(fname,'r') as f:
        return json.load(f)

def remove_None_from_dict(dic):
    return {k: v for k, v in dic.items() if v != None}

def get_states(**kwargs):
    kwargs = remove_None_from_dict(kwargs)
    states = db.session.query(Business.state).filter_by(**kwargs).distinct()
    states = [state[0] for state in states]
    return states

def get_cities(**kwargs):
    kwargs = remove_None_from_dict(kwargs)
    cities = db.session.query(Business.city).filter_by(**kwargs).distinct()
    cities = [city[0] for city in cities]
    return cities

def validate_city(city):
    cities = get_cities()
    return city in cities

def validate_state(state):
    states = get_states()
    return state in states


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)
