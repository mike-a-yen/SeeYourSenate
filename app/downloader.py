from app import db, BASE_DIR
from app.models import *

import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import requests
import urllib.parse as urlparse
import re
import json
import codecs
reader = codecs.getreader('utf-8')

congress_base_url = 'https://www.govtrack.us/data/congress/'
active_base_url = 'http://www.senate.gov/reference/active_bill_type/'


def url_in_db(url):
    if 'bills' in url or 'amendments' in url:
        query = db.session.query(Bill).filter_by(url=url).all()
    elif 'votes' in url:
        query = db.session.query(Bill).filter_by(url=url).all()
    return query != None
        

def url_to_json(url):
    try:
        datapage = requests.get(url)
        data = json.loads(datapage.text)
    except:
        print('***ERROR***',url)
        revisit = os.path.join(BASE_DIR,'data','revisit.txt')
        fo = open(revisit,'a')
        fo.write('%s\n'%url)
        fo.close()
        return 0 
    return data


def save_directory(congress_id,subdir):
    save_dir = os.path.join(BASE_DIR,'data',subdir,
                            congress_id)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    return save_dir


def add_to_json(json_data,**kwargs):
    data = {'raw':json_data}
    for key,value in kwargs.items():
        data[key] = value
    return data
    
def save_json_url(url,**kwargs):
    data = url_to_json(url)
    if not data:
        return None

    filename = save_json_filename(url,data)
    print('Downloading',url,'to',filename)

    json_to_save = add_to_json(data,**{'url':url,'active':False})
    json.dump(json_to_save,open(filename,'w'))
    return filename

def save_json_filename(url,data):
    congress_id = re.search('[0-9]{1,3}',url).group()
    doc = url.split('/')[-2]+'-'+congress_id+'-other'
    doc_id = data.get('bill_id',
                      data.get('amendment_id',
                               data.get('vote_id',
                                        doc)))

    if 'bills' in url:
        save_dir = save_directory(congress_id,'bills')
    elif 'votes' in url:
        save_dir = save_directory(congress_id,'sessions')
    elif 'amendments' in url:
        save_dir = save_directory(congress_id,'amendments')
    else:
        save_dir = save_directory(congress_id,'other')
    filename = os.path.join(save_dir,doc_id+'.json')

    return filename

def save_json(data,filename):
    json.dump(data,open(filename,'w'))
    return filename

def download_json_from_url(url):
    """Recursively download data.json files starting from url"""
    if url.endswith('data.json'):
        print(url)
        save_json_url(url)
        return None
    elif url.endswith(('.xml','.txt')):
        return None
    else:
        try:
            page = requests.get(url)
            print(url)
        except:
            print('***ERROR***',url)
            revisit = os.path.join(BASE_DIR,'data','logs','revisit.txt')
            fo = open(revisit,'a')
            fo.write('%s\n'%url)
            fo.close()
            return None
        soup = BeautifulSoup(page.text,'html.parser')
        links = [link for link in soup.find_all('a') \
                 if link.text not in ['../','text-versions/']]
        for link in links:
            visit_url = os.path.join(url,link.get('href'))
            download_json_from_url(visit_url)


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

def get_bill_url_from_bill_id(bill_id,congress_id):
    base = 'https://www.govtrack.us/data/congress/'
    article_type = get_article_type(bill_id)
    bill_type = get_bill_type(bill_id)
    if bill_type == 'sa':
        bill_id = bill_id.replace('sa','samdt')
        bill_type = 'samdt'
    base = os.path.join(base,str(congress_id),article_type,
                        bill_type,bill_id,'data.json')
    return base

            
def download_from_active_page(congress_id):
    url = 'http://www.senate.gov/reference/active_bill_type/%d.xml'%congress_id
    page = requests.get(url)
    root = ET.fromstring(page.text)
    assert congress_id == int(root.find('congress').text)
    years = list(map(int,root.find('years').text.split('-')))
    date_updated = root.find('date').text

    bills = get_active_senate_bills(root)
    filenames = []
    for name,bill_id in bills:
        url = get_bill_url_from_bill_id(bill_id,congress_id)
        data = url_to_json(url)
        filename = save_json_filename(url,data)
        json_to_save = add_to_json(data,**{'url':url,'active':True})
        save_json(json_to_save,filename)
        filenames.append(filename)
    return filenames


def get_active_senate_bills(xml_root):
    """Returns short bill name and bill_id"""
    bills = []
    items = xml_root.findall('.//item')
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
