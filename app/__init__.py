from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import BASE_DIR

import os
import logging

app = Flask(__name__)

log_file = os.path.join(BASE_DIR,'data','logs','operation.log')
log_handler = logging.FileHandler(filename=log_file)
log_handler.setLevel(logging.INFO)
app.logger.addHandler(log_handler)

#local_db = BASE_DIR+'/tmp/congress.db'
local_db = BASE_DIR+'/tmp/tester.db'
aws_db = 'mysql+pymysql://senator:91f7eacdc792@seeyoursenaterds.clnuzgmorptt.us-west-2.rds.amazonaws.com:3306/seeyoursenatedb'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////'+local_db
#app.config['SQLALCHEMY_DATABASE_URI'] = aws_db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = 'secretsarenofun'

print('DB_URI :',app.config['SQLALCHEMY_DATABASE_URI'])
db = SQLAlchemy(app)

from app import views

