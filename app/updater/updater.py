from app import db, BASE_DIR
from app.models import *

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
active_base_url = 'http://www.senate.gov/reference/active_bill_type/'

def get_congress():
    query = db.session.query(Congress).order_by(Congress.congress_id.desc())
    congress = query.first()
    return congress.congress_id

def get_xml_link(congress_id):
    return os.path.join(active_base_url,str(congress_id)+'.xml')
    
def open_xml_page(bs):
    link = 'http://www.senate.gov'+get_xml_link(bs)
    page = request.urlopen(link)
    return page

def get_bill_type(bill_id):
    return re.findall('[a-z]+',bill_id)[0]

def get_bill_number(bill_id):
    return re.findall('[0-9]+',bill_id)[0]

def get_article_type(bill_id):
    if 'amdt' in bill_id:
        article_type='amendments'
    elif 'sa' in bill_id:
        article_type='amendments'
        bill_id = bill_id.replace('sa','samdt')
    else:
        article_type='bills'
    return article_type

def get_bill_url(bill_id, congress_id):
    base = 'https://www.govtrack.us/data/congress/'
    article_type = get_article_type(bill_id)
    bill_type = get_bill_type(bill_id)
    if bill_type == 'sa':
        bill_id = bill_id.replace('sa','samdt')
        bill_type = 'samdt'
    base = os.path.join(base,str(congress_id),article_type,
                        bill_type,bill_id,'data.json')
    return base

def get_bill_json_from_bill_id(bill_id,congress):
    url = get_bill_url(bill_id,congress)
    print('Getting bill from',url)
    data = url_to_json(url)
    return data

def get_bills(xml_page):
    active = get_active_legislation(xml_page)
    bills = []
    for child in active.getchildren():
        if child.tag == 'item':
            bills.append(child)
    return bills

def get_active_legislation(xml_page):
    root = ET.fromstring(xml_page.read())
    active = None
    for child in root.getchildren():
        if child.tag == 'active_legislation':
            active = child
            return active
        
def parse_active(active):
    """Returns short bill name and bill_id"""
    bills = []
    items = active.findall('item')
    for item in items:
        name = item.find('name').text
        for child in item.getchildren():
            if child.tag in ['house','senate']:
                for article in child.getiterator():
                    if article.tag == 'article':
                        attrib = article.attrib
                        noLink = attrib.get('noLink')=='yes'
                        if article.text != None and not noLink:
                            bill_id = article.text.lower().replace('.','')
                            bills.append((name,bill_id))
    return bills

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
        
def get_congress_url(congress_id):
    """Return the url of the congress_id voting records"""
    return os.path.join(session_base_url,str(congress_id)+'/')

def get_voting_year_url(congress_id,year):
    """Get voting year url pointing towards 
    voting records of that year"""
    url = os.path.join(get_congress_url(congress_id),
                       'votes')
    return os.path.join(url,str(year)+'/')

def get_senate_sessions(congress_id,year):
    latest_voting_year_url = get_voting_year_url(congress_id,year)
    page = request.urlopen(latest_voting_year_url)
    soup = BeautifulSoup(page.read(),'html.parser')
    current_sessions = get_all_session_links(soup)
    return [(code,link) for code,link in current_sessions]

def get_session_urls(congress_id,year):
    year_url = get_voting_year_url(congress_id,year)
    new_sessions = get_senate_sessions(congress_id,year)
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

def url_to_json(url):
    datapage = request.urlopen(url)
    data = json.load(reader(datapage))
    return data

def visit_new_sessions(congress_id,year):
    data_urls = get_session_urls(congress_id,year)
    for url in filter_urls(data_urls):
        data = url_to_json(url)
        yield data

def digest_congress_data(conid):
    congress = db.session.query(Congress).filter_by(congress_id=conid).first()
    if not congress:
        print('New Congress',conid,type(conid))
        congress = Congress(conid,get_congress_url(conid))
        db.session.add(congress)
        db.session.commit()
    return congress

def digest_session_data(session_url):
    session_data = url_to_json(session_url)
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
    url = session_url
    passed = None

    bill_id = session_data.get('vote_id').split('.')[0]

    session = db.session.query(Session)\
              .filter_by(date=date)\
              .filter_by(bill_id=bill_id)\
              .filter_by(chamber=chamber).first()
    if not session:
        session = Session(conid, year, number, chamber, date,
                          bill_id, question, subject, category,
                          requires, passed, url)
        db.session.add(session)
        db.session.commit()
    return session

def digest_vote_data(session_data,session):
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

def digest_bill_data(bill_id,bill_data):
    
    bill_congress = bill_data.get('congress')

    bill_type = get_bill_type(bill_id)
    if bill_type == 'sa':
        bill_type = 'samdt'
            
    bill_number = bill_data.get('number')
    bill_id = bill_type+str(bill_number)+'-'+str(bill_congress)
    bill_title = bill_data.get('official_title')
    bill_short_title = bill_data.get('short_title')
    bill_popular_title = bill_data.get('popular_title')
    bill_topsubject = bill_data.get('subjects_top_term')
    summary = bill_data.get('summary')
    if summary == None:
        summary = {'text':None}
    bill_text = summary['text']

    
    bill = Bill(bill_id, bill_congress,
                bill_type, bill_number,
                bill_title, bill_short_title,
                bill_popular_title, bill_topsubject,
                bill_text,get_bill_url(bill_id,bill_congress))

    billquery = db.session.query(Bill)\
                .filter_by(bill_id=bill.bill_id).first()
    if not billquery:
        db.session.add(bill)
        bill_subjects = bill_data.get('subjects',[])
        for sub in bill_subjects:
            db_subject = BillSubject(bill.bill_id, sub)
            db.session.add(db_subject)
        db.session.commit()
    
    return bill

def populate_db(congress_id,year):
    for session_url in get_session_urls(congress_id,year):
        congress = digest_congress_data(congress_id)
        session = digest_session_data(session_url)
        data = url_to_json(session_url)
        bill = data.get('bill')
        if bill:
            bill_id_short = session.bill_id.split('-')[0]
            print(bill_id_short)
            bill_data = get_bill_json_from_bill_id(bill_id_short,
                                                   congress.congress_id)
            db_bill = digest_bill_data(session.bill_id,bill_data)
            
        digest_vote_data(data,session)

def get_active_bill_data():
    congress_id = get_congress()
    url = get_xml_link(congress_id)
    page = request.urlopen(url)

    root = ET.fromstring(page.read())
    assert congress_id == int(root.find('congress').text)
    years = list(map(int,root.find('years').text.split('-')))
    date_updated = root.find('date').text

    active = root.find('active_legislation')
    bills = parse_active(active)
    
    for name,bill_id in bills:
        bill_data = get_bill_json_from_bill_id(bill_id,congress_id)
        bill = digest_bill_data(bill_id,bill_data)
        bill_id = bill.bill_id
        bill.active = True
        billquery = db.session.query(Bill)\
                    .filter_by(bill_id=bill_id).first()
        if billquery:
            billquery.active = True
        else:
            db.session.add(bill)
            bill_subjects = bill_data.get('subjects',[])
            for sub in bill_subjects:
                db_subject = BillSubject(bill_id, sub)
                db.session.add(db_subject)
        db.session.commit()

        
        filename = os.path.join(BASE_DIR,
                                'data/active_bills',
                                bill_id+'.json')
        print(filename)
        json.dump(bill_data,open(filename,'w'))
    return 'Success!'

if __name__ == '__main__':
    print('Do Something in updater.py')
