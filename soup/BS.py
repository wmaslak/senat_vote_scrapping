#from urllib import request
from bs4 import BeautifulSoup as BS
from datetime import date
import re
#if input("Insert any character to allow scraping over 100 pages. Press enter to limit scraping: "):
#    limit_me = False
#else:
#    limit_me = True
limit_me = False

# get first available vote

n0 = 1
nMax = 10650
# for i in range(1,nMax+1):
#     url = f'https://www.senat.gov.pl/prace/posiedzenia/glosowanie-drukuj,{n}.html'
#     # Look at the page and the code
#     html = request.urlopen(url)
#     bs = BS(html.read(), 'html.parser')
n = 10000
url = f'https://www.senat.gov.pl/prace/posiedzenia/glosowanie-drukuj,{n}.html'
print(url)
    # Look at the page and the code
#html = request.urlopen(url)
from urllib.request import Request, urlopen

req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urlopen(req)

bs = BS(html.read(), 'html.parser')

senators = bs.find_all('div',{'class' : 'senator'})
#print(senators)
for senator in senators:
    print([tag.text.strip('\t\n ') for tag in senator.findChildren()])