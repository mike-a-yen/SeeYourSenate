from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import BASE_DIR
import os

app = Flask(__name__)

local_db = BASE_DIR+'/tmp/dev_congress.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////'+local_db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

print('DB_URI :',app.config['SQLALCHEMY_DATABASE_URI'])
app.config['SECRET_KEY'] = 'secretsarenofun'
db = SQLAlchemy(app)

from app import views


