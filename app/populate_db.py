from app import db, BASE_DIR
from app.models import *

import os
import glob
import json
from datetime import datetime

import logging
log_file = os.path.join(BASE_DIR,'data','logs','database.log')
logging.basicConfig(filename=log_file,level=logging.DEBUG)

def get_doc_id(doc_data):
    if not doc_data:
        print('Error no doc data found! Look at json file!')
        # maybe log something here
        raise Exception('No document in session')
    doc_id = doc_data.get('type')+\
             str(doc_data.get('number'))+'-'+\
             str(doc_data.get('congress'))
    return doc_id

def get_json_data(filepath):
    return json.load(open(filepath,'r'))

def populate_session(session_data):
    url = session_data['url']
    data = session_data['raw']

    category = data.get('category')
    chamber = data.get('chamber')
    congress = data.get('congress')
    date = datetime.strptime(''.join(data['date'].split('-')[:-1]),'%Y%m%dT%H:%M:%S')
    year = date.year
    number = data.get('number')
    question = data.get('question')
    requires = data.get('requires')
    result = data.get('result')
    passed = None # do post processing
    subject = data.get('subject')
    session_type = data.get('type')
    vote_id = data.get('vote_id')
    
    
    doc = data.get('bill',data.get('amendment'))
    if not doc:
        return
    doc_id = get_doc_id(doc)

    session = Session(congress,year,number,
                      chamber,date,doc_id,question,
                      subject,category,requires,
                      result,passed,url)
    db.session.add(session)
    logging.info('Session added: '.join(session.__repr__()))
    db.session.commit()
    logging.info('Session populated: '.join(session.__repr__()))

    session_id = session.session_id
    votes = data.get('votes')
    populate_votes(votes,session_id)

    return

def populate_votes(votes,session_id):
    for vote,members in votes.items():
        for member in members:
            if member == 'VP': continue
            member_id = member.get('id')
            first_name = member.get('first_name')
            last_name = member.get('last_name')
            display_name = member.get('display_name')
            state = member.get('state')
            party = member.get('party')
            member = Member(member_id,
                            first_name,last_name,
                            display_name,
                            state,party)
            
            member_query = db.session.query(Member).filter_by(member_id=member_id).first()
            if not member_query:
                db.session.add(member)
                logging.info('Member added: '.join(member.__repr__()))
            membersession = MemberSession(session_id,member_id,vote)
            db.session.add(membersession)
            logging.info('MemberSession added: '.join(membersession.__repr__()))
            db.session.commit()
            logging.info('Member populated: '.join(member.__repr__()))
            logging.info('MemberSession populated: '.join(membersession.__repr__()))
    return

def populate_bill(bill_data):
    url = bill_data['url']
    data = bill_data['raw']

    bill_id = data.get('bill_id')
    bill_type = data.get('bill_type')
    bill_number = int(data.get('number'))
    congress_id = data.get('congress')
    title = data.get('official_title')
    short_title = data.get('short_title')
    popular_title = data.get('popular_title')
    top_subject = data.get('subjects_top_term')

    summary = data.get('summary',{'text':None})
    if summary != None:
        text = summary.get('text')
    else:
        text = None
    active = bill_data.get('active',False)

    subjects = data.get('subjects')
    
    bill = Bill(bill_id,int(congress_id),
                bill_type,bill_number,
                title, short_title,
                popular_title, top_subject,
                text,url,active=active)

    bill_query = db.session.query(Bill).filter_by(bill_id=bill_id).first()
    if bill_query:
        print('Have it')
        return bill
    
    db.session.add(bill)
    logging.info('Bill added: '.join(bill.__repr__()))
    db.session.commit()
    logging.info('Bill populated: '.join(bill.__repr__()))
    
    for sub in subjects:
        billsubject = BillSubject(bill.bill_id, sub)
        db.session.add(billsubject)
        logging.info('BillSubject added: '.join(billsubject.__repr__()))
        db.session.commit()
        logging.info('BillSubject populated: '.join(billsubject.__repr__()))
    return bill
    
def populate_congress(congress_id):
    query = db.session.query(Congress).filter_by(congress_id=congress_id).first()
    if query:
        return
    else:
        url = 'https://www.govtrack.us/data/congress/%d/'%congress_id
        congress = Congress(congress_id, url)
        db.session.add(congress)
        db.session.commit()
