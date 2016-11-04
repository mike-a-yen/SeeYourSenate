from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os


app = Flask(__name__)

local_db = 'sqlite:////Users/mayen/Programming/WillItPass/tmp/congress.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL',
                                                       local_db)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

print('DB_URI :',app.config['SQLALCHEMY_DATABASE_URI'])
app.config['SECRET_KEY'] = 'secretsarenofun'
db = SQLAlchemy(app)

from app import views
from app.models import *
