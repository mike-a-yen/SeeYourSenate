from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os



from rq import Queue
from rq.job import Job
from worker import conn


app = Flask(__name__)

local_db = 'sqlite:////'+os.path.join(os.getcwd(),'tmp/congress.db')
app.config['SQLALCHEMY_DATABASE_URI'] = local_db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

print('DB_URI :',app.config['SQLALCHEMY_DATABASE_URI'])
app.config['SECRET_KEY'] = 'secretsarenofun'
db = SQLAlchemy(app)

q = Queue(connection=conn)

from app import views
from app.models import *
from app.build_models import build_models

print('#'*50)
print('Building member models')
job = q.enqueue(build_models,
                timeout=1200,
                result_ttl=5000)
print('RQ ID :',job.get_id())
print('Build job set in queue')
print('#'*50)
