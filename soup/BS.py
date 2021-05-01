#from urllib import request
from bs4 import BeautifulSoup as BS
from datetime import date
from urllib.request import Request, urlopen
import re
import pandas as pd

#if input("Insert any character to allow scraping over 100 pages. Press enter to limit scraping: "):
#    limit_me = False
#else:
#    limit_me = True
limit_me = False



n0 = 1
nMax = 10650

voting_id = 10100
voting_url = f'https://www.senat.gov.pl/prace/posiedzenia/glosowanie-drukuj,{voting_id}.html'
#session_day_url =

day_no = 2
session_id = 502
url = f"https://www.senat.gov.pl/prace/posiedzenia/przebieg,{session_id},{day_no},glosowania.html"
print(url)

def get_url_content(url):
	req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	html = urlopen(req)
	bs = BS(html.read(), 'html.parser')
	return(bs)
#bs = get_url_content(url)
#def scrap_single_voting():
#	senators = bs.find_all('div',{'class' : 'senator'})
#	return([tag.text.strip('\t\n ') for tag in senator.findChildren()])
def scrap_single_voting(voting_url):
	try:
		bs = get_url_content(voting_url)
		senators_raw = bs.find_all('div',{'class' : 'senator'})
		senators = [[tag.text.strip('\t\n ') for tag in senator.findChildren()] for senator in senators_raw]
		df = pd.DataFrame(senators)
		df.columns = ["Senator","Vote"]
		return(df)
	except:
		print(f"Problem! Voting's url:\n {url}" )
		


def scrap_day_of_session(session_day_url):
	bs = get_url_content(session_day_url)
	# get session title
	session_title_raw = bs.find('div',{'class' : "meeting-title"})
	session_title = (" ".join(session_title_raw.text.split()))
	
	# get session dates //div[@class='view-element__date']
	session_dates_raw = bs.find('div', {'class' : 'view-element__date'})
	session_dates = (" ".join(session_dates_raw.text.split()))
	
	
	
	if bs.find('div', {'class' : "table-content"}):
		votings_table = bs.find('div', {'class' : "table-content"}).find_all('div', {'class' : "row"})
		votings_rows = [row.find_all('div') for row in votings_table]
		
		# skip every second "row" since its actually part of the same row (possibly optimize this)
		votings_extracted = [[vote[i] for i in [0,1,-1]] for k,vote in enumerate(votings_rows) if k%2==0]
		
		# list of such lists: [# of vote in a day, title, subscript, link to results]
		votings = [[vote[0].get_text(strip = True), vote[1].findChildren()[0].text ,vote[1].p.i.text if vote[1].p else 'NA' ,
		 vote[2].a['href'] ] for vote in votings_extracted]
		
		#print(votings_extracted)
		df = pd.DataFrame(votings)
		df.columns = ["No. of voting","Title","Subscript","Link"]
		df["Session"] = session_title
		df["Dates"] = session_dates
		return(df)
	else:
		return('zonk')
	
	
	

print(scrap_day_of_session(url))

date_string = "11, 12, 13, 17 i 18 sierpnia 2020 r. "		
def parse_date(date_string):
	pass
	

#print(scrap_single_voting(url))
