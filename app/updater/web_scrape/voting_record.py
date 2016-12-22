from app import db
from app.models import *
from app.updater.web_scrape.active_bills import *

import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import urllib.request as request
import urllib.parse as urlparse
import re
import json
import codecs
reader = codecs.getreader('utf-8')

session_base_url = 'https://www.govtrack.us/data/congress/'

def get_all_number_links(soup):
    number_links = []
    for link in soup.find_all('a'):
        num_search = re.search('[0-9]+',link.text)
        if num_search:
            number = int(num_search.group())
            number_links.append((number,link))
    return number_links

def get_all_session_links(soup):
    session_links = []
    for link in soup.find_all('a'):
        s_search = re.search('s[0-9]+',link.text)
        if s_search:
            code = s_search.group()
            session_links.append((code,link))
    return session_links
        
def get_latest_congress_url():
    """Return the url of the latest congress
    voting records
    """
    soup = BeautifulSoup(request.urlopen(session_base_url).read(),
                         'html.parser')
    congresses = get_all_number_links(soup)
    sorted_congresses = sorted(congresses,key=lambda x:x[0])
    latest_congress = sorted_congresses[-1]
    return os.path.join(session_base_url,latest_congress[1]['href'])

def get_latest_voting_year_url():
    """Go to latest congress, then latest voting year
    return url pointing towards latest voting year
    """
    url = os.path.join(get_latest_congress_url(),
                       'votes')
    page = request.urlopen(url)
    soup = BeautifulSoup(page.read(),'html.parser')
    years = sorted(get_all_number_links(soup),key=lambda x: x[0])
    latest_year = years[-1]
    return os.path.join(url,latest_year[1]['href'])

def get_new_senate_sessions():
    latest_voting_year_url = get_latest_voting_year_url()
    year = latest_voting_year_url.split('/')[-1]
    page = request.urlopen(latest_voting_year_url)
    soup = BeautifulSoup(page.read(),'html.parser')
    # sessions on the web page
    current_sessions = get_all_session_links(soup)
    # sessions in the db
    db_sessions = db.session.query(Session)\
                            .filter_by(year=year).all()
    old_sessions = [s.chamber+str(s.number) for s in db_sessions]
    return [(code,link) for code,link in current_sessions if code not in old_sessions]

def scrape_new_sessions():
    year_url = get_latest_voting_year_url()
    new_sessions = get_new_senate_sessions()
    urls = [os.path.join(year_url,link['href'],'data.json')\
            for code,link in new_sessions]
    return urls

def filter_urls(urls):
    go_to_urls = []
    bill_ids = [x.split('/')[-2]+'-'+x.split('/')[-5] for x in urls]
    for url,bill_id in zip(urls,bill_ids):
        if db.session.query(Bill).filter_by(bill_id=bill_id).first():
            continue
        go_to_urls.append(url)
    return go_to_urls
    
def visit_new_sessions():
    data_urls = scrape_new_sessions()
    for url in filter_urls(data_urls):
        data = url_to_json(url)
        yield data

def digest_congress_data(conid):
    congress = db.session.query(Congress).filter_by(congress_id=conid).first()
    if not congress:
        print('New Congress',conid,type(conid))
        congress = Congress(conid)
        db.session.add(congress)
        db.session.commit()
    return congress

def digest_session_data(session_data):
    conid = session_data.get('congress')
    date = datetime.strptime(''.join(session_data['date'].split('-')[:-1]),'%Y%m%dT%H:%M:%S')
    year = date.year
    chamber = session_data.get('chamber')
    number = session_data.get('number')
    category = session_data.get('category')
    question = session_data.get('question')
    requires = session_data.get('requires')
    subject = session_data.get('subject')
    result = session_data.get('result_text')
    passed = None

    bill_id = session_data.get('vote_id').split('.')[0]

    session = db.session.query(Session)\
              .filter_by(date=date)\
              .filter_by(bill_id=bill_id)\
              .filter_by(chamber=chamber).first()
    if not session:
        session = Session(conid, year, number, chamber, date,
                          bill_id, question, subject, category,
                          requires, passed)
        db.session.add(session)
        db.session.commit()
    return session

def digest_vote_data(session_data):
    for vote,people in session_data['votes'].items():
        for person in people:
            if person == 'VP': continue
            memid = person['id']
            first = person['first_name']
            last = person['last_name']
            display = person['display_name']
            state = person['state']
            party = person['party']
            memquery = db.session.query(Member).filter_by(member_id=memid).all()
            if not memquery:
                print('New Member :',display)
                member = Member(memid, first, last, display, state, party)
                db.session.add(member)
                db.session.commit()
                    
            memsess = MemberSession(session.session_id, memid, vote)
            db.session.add(memsess)
            db.session.commit()
    return True

def populate_db():
    for data in visit_new_sessions():
        conid = data.get('congress')
        congress = digest_congress_data(conid)
        session = digest_session_data(data)
        bill = data.get('bill')
        if bill:
            bill_congress = bill.get('congress')
            bill_data = get_bill_json_from_bill_id(session.bill_id,
                                                   congress.congress_id)
            db_bill = digest_bill_data(bill_data)
            billquery = db.session.query(Bill)\
                        .filter_by(bill_id=bill_id).first()
            if not billquery:
                db.session.add(db_bill)
                bill_subjects = bill_data.get('subjects',[])
                for sub in bill_subjects:
                    db_subject = BillSubject(bill_id, sub)
                    db.session.add(db_subject)
                db.session.commit()
        digest_vote_data(data)
        

def url_to_json(url,save=False):
    datapage = request.urlopen(url)
    data = json.load(reader(datapage))
    bill_id = url.split('/')[-2]+'-'+url.split('/')[-5]
    if save:
        json.dumps(data,open('data/bills/'++'.json'))
    return data

if __name__ == '__main__':
    populate_db()
