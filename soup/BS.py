#from urllib import request
from bs4 import BeautifulSoup as BS
from datetime import date
from urllib.request import Request, urlopen
import re
import pandas as pd
import time
from urllib.error import HTTPError

if input("Insert any character to allow scraping over 100 pages. Press enter to limit scraping: "):
    limit_me = False
else:
    limit_me = True
    

#voting_id = 10100
#voting_url = f'https://www.senat.gov.pl/prace/posiedzenia/glosowanie-drukuj,{voting_id}.html'
#session_day_url =


#day_no = 2
#session_id = 502
#url = f"https://www.senat.gov.pl/prace/posiedzenia/przebieg,{session_id},{day_no},glosowania.html"
#print(url)

start = time.time()

def get_url_content(url):
	req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	html = urlopen(req)
	bs = BS(html.read(), 'html.parser')
	return(bs)

#bs = get_url_content(url)
#def scrap_single_voting():
#	senators = bs.find_all('div',{'class' : 'senator'})
#	return([tag.text.strip('\t\n ') for tag in senator.findChildren()])
def scrap_clubs(term_url):
	
	bs = get_url_content(term_url)
	df_total = pd.DataFrame()
	
	# scrap clubs one by one
	members_all = bs.find_all('div', {'class' : re.compile('.*lista-czlonkow.*')})
	for members in members_all:
		club_name = members.parent.parent.find('div', {'class' : re.compile('.*klub-nazwa.*')}).h2.text
		
		club_members = [' '.join(member.text.split()) for member in 
		members.find_all(lambda tag: tag.name == 'div' and not tag.attrs)]
		
		df_club = pd.DataFrame(club_members)
		df_club.columns = ['name']
		df_club['club'] = club_name
		
		df_total = pd.concat([df_total, df_club], axis = 0)
		
	return(df_total)
	
def scrap_single_voting(voting_url):

	bs = get_url_content(voting_url)
	senators_raw = bs.find_all('div',{'class' : 'senator'})
	senators = [[tag.text.strip('\t\n ') for tag in senator.findChildren()] for senator in senators_raw]
	df = pd.DataFrame(senators)
	df.columns = ["Senator","Vote"]
	
	return(df)


def scrap_day_of_session(session_day_url):

	bs = get_url_content(session_day_url)	
	
	if not isinstance(bs, str) and bs.find('div', {'class' : "table-content"}):
		
		# get session title
		session_title_raw = bs.find('div',{'class' : "meeting-title"})
		session_title = (" ".join(session_title_raw.text.split()))
		
		# get session dates //div[@class='view-element__date']
		session_dates_raw = bs.find('div', {'class' : 'view-element__date'})
		session_dates = (" ".join(session_dates_raw.text.split()))
		
		votings_table = bs.find('div', {'class' : "table-content"}).find_all('div', {'class' : "row"})
		votings_rows = [row.find_all('div') for row in votings_table]
		
		# skip every second "row" since its actually part of the same row (possibly optimize this)
		votings_extracted = [[vote[i] for i in [0,1,-1]] for k,vote in enumerate(votings_rows) if k%2==0]
		
		# list of such lists: [# of vote in a day, title, subscript, link to results]
		#votings = [[vote[0].get_text(strip = True), vote[1].findChildren()[0].text ,vote[1].p.i.text if vote[1].p else 'NA' ,
		 #vote[2].a['href'] ] for vote in votings_extracted]
		
		votings = []
		for vote in votings_extracted:
			no_of_voting = vote[0].get_text(strip = True)
			title = vote[1].findChildren()[0].text 
			subscript = vote[1].p.i.text if vote[1].p else 'NA' 
			link = vote[2].a['href'] 
			voting_id = link[link.find(',')+1:link.find('.html')]
			votings.append([no_of_voting,
					title,
					subscript,
					link,
					voting_id])
		#print(votings_extracted)
		df = pd.DataFrame(votings)
		df.columns = ["No. of voting","Title","Subscript","Link","voting_id"]
		df["Session"] = session_title
		df["Dates"] = session_dates
		return(df)
	else:
		return(False)

# scrap Senate sessisons for dates, linkts to votings and votings' titles
session_min = 10
session_max = 556
to_scrap = session_max - session_min
scrapped = 0

out_csv = 'output/sessions.csv'
print(f'Total sessions to scrap:{to_scrap}')


for counter,session_id in enumerate(range(session_min,session_max+1)):
	try:		
		print(f'************* Session {counter} of {to_scrap}. Current session id:{session_id}')
		print(f'No. of total scrapped pages: {scrapped}')
		
		day_no = 1
		session_day_url = f"https://www.senat.gov.pl/prace/posiedzenia/przebieg,{session_id},{day_no},glosowania.html"
		
		while isinstance(scrap_day_of_session(session_day_url),pd.DataFrame):
			#print(f'Current day:{day_no}\n')
			if scrapped == 0:
				scrap_day_of_session(session_day_url).to_csv(out_csv,index=False,header=True)
				day_no += 1
				scrapped += 1
				
			else:
				scrap_day_of_session(session_day_url).to_csv(out_csv, index=False, header=False, mode='a')
				day_no += 1
				scrapped += 1
			session_day_url = f"https://www.senat.gov.pl/prace/posiedzenia/przebieg,{session_id},{day_no},glosowania.html"
			if limit_me and scrapped == 100:
				break
		
		if limit_me and scrapped == 100:
			break
	except HTTPError:
			with open('output/log_unscrapped_sessions.txt', 'a') as f:
				f.write(f', {session_id}')
			print(f'HTTPError for session_id: {session_id}\n Moving on!')
			continue
			
print('Done with sessions!\n')


# get saved links to votings and scrap every voting for votes

voting_links = pd.read_csv('output/sessions.csv' , usecols = ['Link','voting_id'])
total_votings = voting_links.shape[0]
counter = 0 
for voting_url, vote_id in zip(voting_links.Link, voting_links.voting_id):
	print(f'scraping vote {counter} out of {total_votings}')
	try:
		votes = scrap_single_voting(voting_url)
		
		if counter == 0:
			df = scrap_single_voting(voting_url)
			df['voting_id'] = vote_id
			df.to_csv('output/votes.csv',index=False,header=True)
			counter += 1
		else:
			df = scrap_single_voting(voting_url)
			df['voting_id'] = vote_id
			df.to_csv('output/votes.csv',index=False,header=False,mode='a')
			counter += 1
		
	except HTTPError:
		with open('output/log_unscrapped_votes.txt', 'a') as f:
			f.write(f', {voting_url}')
			print(f'HTTPError for voting url: {voting_url}\n Moving on!')
		continue

# get party affiliation for all considered terms 
possible_terms = [8,9,10]
df_all_terms = pd.DataFrame()
for i,term in enumerate(possible_terms):
	
	try:
		term_df = scrap_clubs(f'https://www.senat.gov.pl/sklad/kluby-i-kolo/?kadencja={term}')
		term_df['Term number'] = term
		
		df_all_terms = pd.concat([df_all_terms,term_df],axis=0)
		if enumerate == 0:
			df_all_terms.to_csv('output/clubs.csv',index=False,header=True)
		else:
			df_all_terms.to_csv('output/clubs.csv',index=False,header=False, mode = 'a')
		
	except:
		print(f'Some problem with term {term}. Moving on!')
		continue
	
end = time.time()
print(f'Elapsed time: {end - start}')
# votings: Elapsed time: 5145.422218084335
# sessions: Elapsed time: 359.7456362247467

		
		
#with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#    print(scrap_day_of_session(url))

#date_string = "11, 12, 13, 17 i 18 sierpnia 2020 r. "		
#def parse_date(date_string):
#	pass
	

#print(scrap_single_voting(url))
