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

base_url = 'https://www.govtrack.us/data/congress/'


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
    soup = BeautifulSoup(request.urlopen(base_url).read(),
                         'html.parser')
    congresses = get_all_number_links(soup)
    sorted_congresses = sorted(congresses,key=lambda x:x[0])
    latest_congress = sorted_congresses[-1]
    return urlparse.urljoin(base_url,latest_congress[1]['href'])

def get_latest_voting_year_url():
    """Go to latest congress, then latest voting year
    return url pointing towards latest voting year
    """
    url = os.path.join(get_latest_congress_url(),
                       'votes')
    page = request.urlopen(url)
    soup = BeautifulSoup(page.read(),'lxml-xml')
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

    # filter urls by bills already in DB
    # TODO: refactor
    go_to_urls = []
    bill_ids = [x.split('/')[-2]+'-'+x.split('/')[-5] for x in go_to_urls]
    for url,bill_id in zip(urls,bill_ids):
        if db.session.query(Bill).filter_by(bill_id=bill_id).first():
            continue
        go_to_urls.append(url)
    return go_to_urls
    
def visit_new_sessions():
    data_urls = scrape_new_sessions()
    for url in data_urls:
        data = url_to_json(url)
        yield data
            
def populate_db():
    for data in visit_new_sessions():
        congress = data.get('congress')
        conquery = db.session.query(Congress).filter_by(congress_id=conid).all()
        if not conquery:
            print('New Congress',conid)
            congress = Congress(conid)
            #db.session.add(congress)
            #db.session.commit()
                
        date = datetime.strptime(''.join(data['date'].split('-')[:-1]),'%Y%m%dT%H:%M:%S')
        year = date.year
        chamber = data.get('chamber')
        number = data.get('number')
        category = data.get('category')
        question = data.get('question')
        requires = data.get('requires')
        subject = data.get('subject')
        result = data.get('result_text')
        passed = None
            
        bill = data.get('bill')
        if bill:
            bill_congress = bill.get('congress')
            bill_data = self.get_bill_json(bill)
            bill_type = bill.get('type')
            bill_number = bill.get('number')
            bill_id = bill_type+str(bill_number)+'-'+str(bill_congress)
            bill_title = bill_data.get('official_title')
            bill_topsubject = bill_data.get('subjects_top_term')
            bill_text = bill_data.get('summary',{'text':None})['text']
            bill_subjects = bill_data.get('subjects',[])
            
            billquery = db.session.query(Bill).filter_by(bill_id=bill_id).all()
            if not billquery:
                print('New Bill',bill_id)
                db_bill = Bill(bill_id, bill_congress,
                               bill_type, bill_number,
                               bill_title, bill_topsubject, bill_text)
                #db.session.add(db_bill)
                for sub in bill_subjects:
                    db_subject = BillSubject(bill_id, sub)
                    #db.session.add(db_subject)

            session = Session(conid, year, number, chamber, date,
                              bill_id, question, subject, category,
                              requires, passed)
            #db.session.add(session)
            #db.session.commit()

            for vote,people in raw['votes'].items():
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
                        #db.session.add(member)
                        #db.session.commit()
                    
                    memsess = MemberSession(session.session_id, memid, vote)
                    #db.session.add(memsess)
                    #db.session.commit()
        

def url_to_json(url,save=False):
    datapage = request.urlopen(url)
    data = json.loads(datapage.read())
    bill_id = url.split('/')[-2]+'-'+url.split('/')[-5]
    if save:
        json.dumps(data,open('data/bills/'++'.json'))
    return data

def bill_type(self,bill_id):
    return re.findall('[a-z]+',bill_id)[0]
    
def bill_number(self,bill_id):
    return re.findall('[0-9]+',bill_id)[0]

def get_bill_json(self,bill,save=False):
    """bill is a dictionary"""
    base_url = 'https://www.govtrack.us/data/congress/'
    type = bill['type']
    number = str(bill['number'])
    congress = str(bill['congress'])
    bill_id = type+number+'-'+congress
    data_url = urlparse.urljoin(base_url,os.path.join(congress,
                                                      'bills',
                                                      type,
                                                      type+number,
                                                      'data.json'))
    datapage = request.urlopen(data_url)
    data = json.load(reader(datapage))
    if save:
        json.dumps(data,open('data/bills/'+bill_id+'.json','w'))
    return data
                                    
                                    
