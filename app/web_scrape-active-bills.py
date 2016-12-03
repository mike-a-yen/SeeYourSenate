import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import urllib.request as request
import urllib.parse as urlparse
import re
import json
import codecs
reader = codecs.getreader('utf-8')

base_url = 'http://www.senate.gov/legislative/active_leg_page.htm'

def get_congress(bs):
    for div in bs.findAll('div',{'class':'contenttitle'}):
        if 'Congress' in div.text:
            match = re.search('^[0-9]+',div.text)
            if match:
                span = match.span()
                return match.string[span[0]:span[1]]

def get_xml_link(bs):
    for link in bs.findAll('a'):
        url = link.get('href','')
        if '.xml' in url:
            return url
        return None
    
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
    base += os.path.join(congress,
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
        
def parse_bill_ids(bills):
    bill_ids = []
    for bill in bills:
        for child in bill.getchildren():
            if child.tag in ['senate','house']:
                if child.find('article') != None:
                    if child.find('article').text != None:
                        bill_id = child.find('article').text.lower().replace('.','')
                        if 'veto' not in bill_id:
                            bill_ids.append(bill_id)
    return bill_ids

if __name__ == '__main__':
    page = request.urlopen(base_url)
    bs = BeautifulSoup(page.read(),'lxml')

    congress_id = get_congress(bs)
    xml_page = open_xml_page(bs)
    bills = get_bills(xml_page)
    bill_ids = parse_bill_ids(bills)
    for bill_id in bill_ids:
        bill_data = get_bill_json_from_bill_id(bill_id,congress)

        bill_congress = congress
        bill_type = bill_data['type']
        bill_number = bill_data['number']
        bill_id = bill_type+str(bill_number)+'-'+str(bill_congress)
        
        bill_title = bill_data['official_title']
        bill_topsubject = bill_data['subjects_top_term']
        bill_text = bill_data['summary']['text']
        bill_subjects = bill_data['subjects']

        billquery = db.session.query(Bill).filter_by(bill_id=bill_id).all()
        if not billquery:
            print('New Bill',bill_id)
            db_bill = Bill(bill_id, bill_congress,
                           bill_type, bill_number,
                           bill_title, bill_topsubject,
                           bill_text,active=True)
            db.session.add(db_bill)
            for sub in bill_subjects:
                db_subject = BillSubject(bill_id, sub)
                db.session.add(db_subject)

        filename = os.path.join(BASEDIR,
                                'data/active_bills',
                                bill_id+'.json')
        json.dump(bill_data,open(filename))
        
