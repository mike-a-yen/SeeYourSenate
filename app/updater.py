from app import db, BASE_DIR
from app.models import *
from app.downloader import download_json_from_url
from app.populate_db import populate_bill, populate_session, get_json_data

import os
import glob

base_url = 'https://www.govtrack.us/data/congress/'
active_base_url = 'http://www.senate.gov/reference/active_bill_type/'

def congress_url(congress_id):
    return os.path.join(base_url,str(congress_id))

def update_congress(congress_id):
    url = congress_url(congress_id)
    download_json_from_url(url)
    bill_files = glob.glob(os.path.join(BASE_DIR,'data','bills',
                                        str(congress_id),'*.json'))
    session_files = glob.glob(os.path.join(BASE_DIR,'data','sessions',
                                        str(congress_id),'*.json'))
    amendment_files = glob.glob(os.path.join(BASE_DIR,'data','sessions',
                                        str(congress_id),'*.json'))

    for bill_file in bill_files:
        data = get_json_data(bill_file)
        populate_bill(data)

    for session_file in session_files:
        data = get_json_data(session_file)
        populate_session(data)


def update_active(congress_id):
    #TODO: deactivate all active bills
    active_bill_files = download_from_active_page(congress_id)
    for active_file in active_bill_files:
        data = get_json_data(active_file)
        populate_bill(data)
    
