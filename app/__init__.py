from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import BASE_DIR

import os

app = Flask(__name__)


local_db = BASE_DIR+'/tmp/congress.db'
#local_db = BASE_DIR+'/tmp/tester.db'
aws_db = 'mysql+pymysql://senator:91f7eacdc792@seeyoursenatedb.clnuzgmorptt.us-west-2.rds.amazonaws.com:3306/seeyoursenatedb'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////'+local_db
#app.config['SQLALCHEMY_DATABASE_URI'] = aws_db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = 'secretsarenofun'

print('DB_URI :',app.config['SQLALCHEMY_DATABASE_URI'])
db = SQLAlchemy(app)

from app import views

