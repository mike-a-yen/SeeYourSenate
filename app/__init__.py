from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

application = Flask(__name__)

local_db = 'sqlite:////'+os.path.join(os.getcwd(),'tmp/congress.db')
application.config['SQLALCHEMY_DATABASE_URI'] = local_db
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

print('DB_URI :',application.config['SQLALCHEMY_DATABASE_URI'])
application.config['SECRET_KEY'] = 'secretsarenofun'
db = SQLAlchemy(application)



from app import views
