from . import db
from datetime import datetime

class Congress(db.Model):
    __tablename__ = 'congress'
    congress_id = db.Column('congress_id',db.Integer,primary_key=True)
    
    def __init__(self, congress_id):
        self.congress_id = congress_id

class Session(db.Model):
    __tablename__ = 'session'
    id = db.Column('session_id',db.Integer, primary_key=True)
    congress_id = db.Column('congress_id',
                            db.ForeignKey('congress.congress_id'))
    year = db.Column('year', db.Integer)
    number = db.Column('number', db.Integer)
    chamber = db.Column('chamber', db.String(20))
    date = db.Column('date', db.DateTime)
    bill_id = db.Column('bill_id',db.ForeignKey('bill.bill_id'))
    question = db.Column('question', db.String(240))
    subject = db.Column('subject', db.String(240))
    category = db.Column('category', db.String(240))
    requires = db.Column('requires', db.String(10))
    passed = db.Column('passed', db.Integer)

    def __init__(self, congress_id, year, number, chamber,
                 date, bill_id, question, subject,
                 category, requires, passed):
        
        self.congress_id = congress_id
        self.year = year 
        self.number = number
        self.chamber = chamber
        self.date = date
        self.bill_id = bill_id
        self.question = question
        self.subject = subject
        self.category = category
        self.requires = requires
        self.passed = passed

class Bill(db.Model):
    __tablename__ = 'bill'
    id = db.Column('bill_id',db.Integer, primary_key=True)
    type = db.Column('type', db.String(80))
    title = db.Column('title',db.String(240))
    purpose = db.Column('purpose', db.String(240))
    bill_text_path = db.Column('bill_text_path',db.String(240))

    def __init__(self, type, title, purpose, bill_text_path):
        self.type = type
        self.title = title
        self.purpose = purpose
        self.bill_text_path = bill_text_path


class MemberSession(db.Model):
    __tablename__ = 'membersession'
    id = db.Column('id', db.Integer, primary_key=True)
    session_id = db.Column('session_id', db.ForeignKey('session.session_id'))
    member_id = db.Column('member_id', db.ForeignKey('member.member_id'))
    vote = db.Column('vote', db.Integer)

    def __init__(self, session_id, member_id, vote):
        self.session_id = session_id
        self.member_id = member_id
        self.vote = vote

        
class Member(db.Model):
    __tablename__ = 'member'
    id = db.Column('member_id',db.String(20), primary_key=True)
    first_name = db.Column('first',db.String(40))
    last_name = db.Column('last',db.String(40))
    display_name = db.Column('display',db.String(80))
    state = db.Column('state',db.String(40))
    party = db.Column('party',db.String(20))
    nn_model_path = db.Column('nn_model_path',db.String(40))
    vectorizer_path = db.Column('vectorizer_path',db.String(40))

    def __init__(self, id, first, last, display, state, party,
                 nn_model_path=None, vectorizer_path=None):
        self.id = id
        self.first_name = first
        self.last_name = last
        self.display_name = display
        self.state = state
        self.party = party
        self.nn_model_path = nn_model_path
        self.vectorizer_path = vectorizer_path

if __name__ == '__main__':
    print('Creating DB')
    db.create_all()
