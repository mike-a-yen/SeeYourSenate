from app import app, db, BASE_DIR
from app.models import *
from app.member_topics import vote_topic_freq
from app.build_models import positive_negative_subjects
from app.model_prediction import senate_prediction
from app.utils import (get_random_member,
                       get_senate,
                       get_active_bills)
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
    
    if flask.request.method == 'POST':
        print(flask.request.form['senator'])
        member_request = flask.request.form['senator']
        member = db.session.query(Member)\
                           .filter(Member.display_name==member_request)\
                           .first()
    else:
        member = get_random_member()
        
    memid = member.member_id
    print('member id:',memid)
    clouds = make_word_cloud(member)

    yay_subjects, nay_subjects = positive_negative_subjects(memid)
    return flask.render_template('senator.html',
                                 senators=display_names,
                                 first_name=member.first_name,
                                 last_name=member.last_name,
                                 state=member.state,
                                 party=member.party,
                                 yay_cloud=clouds['Yea'],
                                 nay_cloud=clouds['Nay'],
                                 yay_subjects=yay_subjects,
                                 nay_subjects=nay_subjects)

@app.route('/active')
def active():
    #active_bills = get_active_bills()
    #votes = senate_prediction(get_senate(),active_bills)
    #aggregate_votes = np.apply_along_axis(np.bincount,0,votes)
    #bill_summary = list(zip(active_bills,aggregate_votes.T))
    #active_bills = [{'bill_id':bill.type.upper()+str(bill.number),
    #                 'top_subject':bill.top_subject,
    #                 'votes_for':vote[1],
    #                 'votes_against':vote[0],
    #                 'passed':vote[1]>vote[0]} for bill,vote in bill_summary]
    active_bills = pickle.load(open(os.path.join(BASE_DIR,'data/active_bill_predictions.pklb'),'rb'))
    return flask.render_template('active_bills.html',
                                 active_bills=active_bills)
