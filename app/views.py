from app import app
from app.preprocessing import xy, clusters, votes
import flask

@app.route('/')
@app.route('/index')
def index():
    cluster_plot = open('app/static/img/cluster.html','r').read()
    return flask.render_template('index.html',
                                 cluster_plot=cluster_plot)
