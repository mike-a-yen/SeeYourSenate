from app import db
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
            session_links.append(code,link)
    return session_links

class LatestVotingRecord(object):
    def __init__(self):
        self.base_url = 'https://www.govtrack.us/data/congress/'
        self.base_page = request.urlopen(self.base_url)
        
    def get_latest_congress_url(self):
        """Return the url of the latest congress
        voting records
        """
        soup = BeautifulSoup(self.base_page.read(),'html.parser')
        congresses = get_all_number_links(soup)
        sorted_congresses = sorted(congresses,key=lambda x:x[0])
        latest_congress = sorted_congresses[-1]
        return urlparse.urljoin(base_url,latest_congress[1]['href'])

    def get_latest_voting_year_url(self):
        url = self.get_latest_congress_url()
        page = request.urlopen(url)
        soup = BeautifulSoup(page.read(),'html.parser')
        years = sorted(get_all_number_links(soup),key=lambda x: x[0])
        latest_year = years[-1]
        return urlparse.urljoin(url,latest_year['href'])

    def get_new_senate_sessions(self):
        latest_voting_year_url = self.get_latest_voting_year_url()
        year = latest_voting_url.split('/')[-1]
        
        page = request.urlopen(latest_voting_year_url)
        soup = BeautifulSoup(page.read,'html.parser')
        # sessions on the web page
        current_sessions = get_all_session_links(soup)

        # sessions in the db
        db_sessions = db.session.query(Session)\
                      .filter_by(year=year).all()
        old_sessions = [s.chamber+str(s.number) for s in db_sessions]
        return [(code,link) for code,link in current_sessions if code not in old_sessions]

    def scrape_new_sessions(self):
        year_url = self.get_latest_voting_year_url()
        new_sessions = self.get_new_senate_sessions()
        go_to_urls = [urlparse.urljoin(year_url,link['href'],'data.json')\
                      for code,link in new_sessions]
        
