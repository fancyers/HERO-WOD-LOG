import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient

client = MongoClient('mongodb://15.165.203.11', 27017, username="test", password="test")
db = client.namedwods

headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
data = requests.get('https://www.crossfit.com/heroes',headers=headers)

soup = BeautifulSoup(data.text, 'html.parser')

divs = soup.select('#main > div')

for div in divs:
    name = div.select_one('div > h3> strong')
    if name is None: continue
    final_name = name.text.strip()

    content = div.select_one('div > p')
    type = content.text.splitlines()[0]
    if type == ' ': continue
    final_type = type

    contents = content.text.splitlines()[1:]
    txt = ''
    for cont in contents:
        txt += '<li>' + cont + '</li>'
    if txt == '': continue
    final_content = txt

    img = div.select_one('img')['src']

    doc = {
        'name': final_name,
        'type': final_type,
        'content': final_content,
        'img': img
    }

    db.wod_info.insert_one(doc)



