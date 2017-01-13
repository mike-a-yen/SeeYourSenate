from app import db, BASE_DIR
from app.models import *

import networkx as nx

"""
Create a network for senators to find groups that have similar voting patterns
For each session, split the members by their vote
For each unique member pair who casts vote, increment their edge weight by 1

"""
