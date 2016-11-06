from app import app, db
from app.models import *
from app.preprocessing import xy, clusters, votes
from app.member_topics import vote_topic_freq
from app.utils import get_random_member
from app.cloud import make_word_cloud

import flask

import numpy as np

import matplotlib.pyplot as plt
import mpld3


@app.route('/')
@app.route('/index')
def index():
    cluster_plot = open('app/static/img/cluster.html','r').read()
    stats_plot = open('app/static/img/model_performance.html','r').read()
    return flask.render_template('index.html',
                                 cluster_plot=cluster_plot,
                                 stats_plot=stats_plot)

@app.route('/senator',methods=['GET','POST'])
def senator():
    member = get_random_member()
    if flask.request.method == 'POST':
        pass
    memid = member.id
    topic = vote_topic_freq(memid)
    
    clouds = {key:mpld3.fig_to_html(make_word_cloud(words,key))\
              for key,words in topic.items()}

    return flask.render_template('senator.html',
                                 first_name=member.first_name,
                                 last_name=member.last_name,
                                 state=member.state,
                                 party=member.party,
                                 yay_cloud=clouds['Yea'],
                                 nay_cloud=clouds['Nay'])
