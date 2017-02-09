from app import app, db, BASE_DIR
from app.models import *
from app.member_topics import vote_topic_freq
from app.member_utils import vote_map, member_vote_subject_bill_table
from app.build_models import positive_negative_subjects, voting_subject_record
from app.model_prediction import senate_prediction
from app.utils import (get_random_member,
                       get_senate,
                       get_active_bills,
                       bill_display_title)
from app.cloud import make_word_cloud, save_member_cloud

import os
import flask
import pandas as pd
import numpy as np
import pickle

import matplotlib.pyplot as plt
import mpld3


@app.route('/')
@app.route('/index')
def index():
    return flask.render_template('index.html')

@app.route('/details')
def details():
    return flask.render_template('details.html')

@app.route('/preliminary')
def preliminary():
    cluster_plot = open(BASE_DIR+'/app/static/img/cluster.html','r').read()
    stats_plot = open(BASE_DIR+'/app/static/img/model_performance.html','r').read()
    return flask.render_template('preliminary.html',
                                 cluster_plot=cluster_plot,
                                 stats_plot=stats_plot)

@app.route('/contact')
def contact():
    return flask.render_template('contact_info.html')
    
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
        #serve Mitch McConnell
        member = db.session.query(Member).filter_by(member_id='S174').first()
        
    memid = member.member_id
    print('member id:',memid)
    clouds = make_word_cloud(member)

    subjects = voting_subject_record(memid)
    return flask.render_template('senator.html',
                                 senators=display_names,
                                 first_name=member.first_name,
                                 last_name=member.last_name,
                                 state=member.state,
                                 party=member.party,
                                 memid=member.member_id,
                                 yay_cloud=clouds['Yea'],
                                 nay_cloud=clouds['Nay'],
                                 subjects=subjects)

@app.route('/subject_view/<subject>/<member_id>')
def subject_view(subject,member_id):
    member = db.session.query(Member).filter_by(member_id=member_id).first()

    vote_subjects = member_vote_subject_bill_table(member_id,subject)
    vote_subjects['bill_id'] = vote_subjects['bill_id'].apply(str.upper)
    return flask.render_template('subject_view.html',
                                 first_name=member.first_name,
                                 last_name=member.last_name,
                                 subject=subject,
                                 n=len(vote_subjects),
                                 bills=vote_subjects.T.to_dict().values())


@app.route('/bill_summary/<bill_id>')
def bill_summary(bill_id):
    bill = db.session.query(Bill).filter_by(bill_id=bill_id.lower()).first()
    display_title = bill_display_title(bill)
    return flask.render_template('bill_summary.html',
                                 bill=bill,
                                 display_title=display_title)

@app.route('/active')
def active():
    active_bills = pickle.load(open(os.path.join(BASE_DIR,
                                    'data/active_bill_predictions.pklb'),
                                    'rb'))
    return flask.render_template('active_bills.html',
                                 active_bills=active_bills)

@app.route('/bill')
def bill():
    bill_id = flask.request.args.get('bill_id')
    id = bill_id.lower()+'-114'

    print('bill',id)
    print(bill_id)
    billquery = db.session.query(Bill).filter_by(bill_id=id)
    bill = billquery.first()

    session = db.session.query(Session)\
              .filter(Session.bill_id==id)\
              .order_by(Session.number.desc())\
              .order_by(Session.date.desc()).first()

    if session:
    
        votes = db.session.query(Member.first_name,Member.last_name,Member.state,Member.party,
                                 MemberSession.vote)\
                          .filter(Member.member_id==MemberSession.member_id)\
                          .filter(MemberSession.session_id==session.session_id)\
                          .filter(Session.number==session.number)\
                          .filter(Session.bill_id==id)\
                          .order_by(Member.state.asc(),
                                    Member.party.asc(),
                                    Member.last_name.asc()).all()
    else:
        flask.flash('Something went wrong, bill data can not be retreved.')
        return flask.redirect(flask.url_for('active'))
    vote_record = pd.DataFrame(votes,columns=['first_name','last_name','state','party','vote'])
    vote_record['vote'] = vote_record['vote'].apply(vote_map)
    vote_record = vote_record.T.to_dict().values()
    vote_record = sorted(vote_record,key=lambda x:(x['state'],x['party'],x['last_name']))
    return flask.render_template('bill.html',
                                 display_title=bill_id,
                                 bill=bill,
                                 votes=vote_record)

@app.route('/groups')
def groups():
    graph_plot = open(os.path.join(BASE_DIR,'app/static/img/party_graph.html')).read()
    return flask.render_template('groups.html',
                                 graph=graph_plot)
