from app import BASE_DIR
import os
from bs4 import BeautifulSoup
import wget
import glob
import subprocess

def gutenberg_html_pages():
    save_dir = os.path.join(BASE_DIR,'data/extra_texts/')
    wget_command = """wget -w 2 -m 
    http://www.gutenberg.org/robot/harvest?filetypes[]=txt&langs[]=en 
    %s"""%(save_dir)
    subprocess.call(wget_command,shell=True)

def get_urls_from_html_file(zip_file):
    soup = BeautifulSoup(open(zip_file).read(),'html.parser')
    hrefs = map(lambda x: x.get('href'), soup.find_all('a'))
    return filter(lambda x: x.endswith('.zip'),hrefs)

def download_gutenberg_zips(html_file_dir,
                            save_dir=os.path.join(BASE_DIR,'data/extra_texts/')):
    files = glob.glob(os.path.join(html_file_dir,'*txt'))
    url_banks = [get_urls_from_html_file(fname) for fname in files]
    [wget.download(url,out=save_dir) for url_bank in url_banks for url in url_bank]
