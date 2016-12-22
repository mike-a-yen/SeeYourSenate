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

base_url = 'http://www.senate.gov/reference/active_bill_type/'

def get_congress():
    query = db.session.query(Congress).order_by(Congress.congress_id.desc())
    congress = query.first()
    return congress.congress_id

def get_xml_link(congress_id):
    return os.path.join(base_url,str(congress_id)+'.xml')
    
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

def generate_data_url(bill_id, congress):
    base = 'https://www.govtrack.us/data/congress/'
    article_type = get_article_type(bill_id)
    bill_type = get_bill_type(bill_id)
    if bill_type == 'sa':
        bill_id = bill_id.replace('sa','samdt')
        bill_type = 'samdt'
    base = os.path.join(base,
                        str(congress),
                        article_type,
                        bill_type,
                        bill_id,
                        'data.json')
    return base

def get_bill_json_from_bill_id(bill_id,congress):
    url = generate_data_url(bill_id,congress)
    print(url)
    datapage = request.urlopen(url)
    data = json.load(reader(datapage))
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
        
    db_bill = Bill(bill_id, bill_congress,
                   bill_type, bill_number,
                   bill_title, bill_short_title,
                   bill_popular_title, bill_topsubject,
                   bill_text)
    return db_bill

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
    get_active_bill_data()
