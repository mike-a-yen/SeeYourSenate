from app import app
from app.preprocessing import xy, clusters, votes
import flask
from datetime import datetime
from app.cluster import plot_2d, plot_3d

@app.route('/')
@app.route('/index')
def index():
    cluster_plot = plot_2d(xy, clusters, votes)
    return flask.render_template('index.html',
                                 cluster_plot=cluster_plot)
