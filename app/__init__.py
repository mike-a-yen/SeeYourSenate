from flask import Flask
import os

app = Flask(__name__)

from app import utils, views
from app.preprocessing import tfidf_matrix, xy, clusters
