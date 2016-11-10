from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import BASE_DIR
print('We are in:', BASE_DIR)
import os

print('IN INIT')

app = Flask(__name__)

local_db = '/var/www/html/WillItPass/tmp/congress.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////'+local_db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

print('DB_URI :',app.config['SQLALCHEMY_DATABASE_URI'])
app.config['SECRET_KEY'] = 'secretsarenofun'
db = SQLAlchemy(app)
print('Loaded DB')

print('Next is views')
from app import views
print('Imported VIEWS')
