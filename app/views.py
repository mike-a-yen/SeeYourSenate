from app import app, db, BASE_DIR
from app.models import *
from app.member_topics import vote_topic_freq
from app.utils import get_random_member,get_senate
from app.cloud import make_word_cloud, save_member_cloud

import os
import flask

import numpy as np
import pickle

import matplotlib.pyplot as plt
import mpld3


@app.route('/')
@app.route('/index')
def index():
    cluster_plot = open(BASE_DIR+'/app/static/img/cluster.html','r').read()
    stats_plot = open(BASE_DIR+'/app/static/img/model_performance.html','r').read()
    return flask.render_template('index.html',
                                 cluster_plot=cluster_plot,
                                 stats_plot=stats_plot)

@app.route('/senator',methods=['GET','POST'])
def senator():
    senate_members = get_senate()
    display_names = list(map(lambda x: x.display_name, senate_members))
    
    member = get_random_member()
    model = pickle.load(open(os.path.join(BASE_DIR,member.nn_model_path),'rb'))
    vectorizer = pickle.load(open(os.path.join(BASE_DIR,member.vectorizer_path),'rb'))
    
    if flask.request.method == 'POST':
        print(flask.request.form['senator'])
        member_request = flask.request.form['senator']
        member = db.session.query(Member)\
                    .filter(Member.display_name==member_request)\
                    .first()
        
    memid = member.id
    topic = vote_topic_freq(memid)    
    clouds = {key:make_word_cloud(words,key)\
              for key,words in topic.items()}

    # save clouds
    paths = {key:save_member_cloud(fig,member,key)\
             for key,fig in clouds.items()}
        
    return flask.render_template('senator.html',
                                 senators=display_names,
                                 first_name=member.first_name,
                                 last_name=member.last_name,
                                 state=member.state,
                                 party=member.party,
                                 yay_cloud=paths['Yea'],
                                 nay_cloud=paths['Nay'])
