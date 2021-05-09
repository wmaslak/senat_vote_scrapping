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

start = time.time()

def get_url_content(url):
	'''
	function that returns BS object from given link
	'''
	req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	html = urlopen(req)
	bs = BS(html.read(), 'html.parser')
	return(bs)

def scrap_clubs(term_url):
	'''
	function that scraps club affiliations given an URL
	returns a dataframe with names of MPs and their respective clubs in each term of office
	'''
	bs = get_url_content(term_url)
	df_total = pd.DataFrame()
	
	# scrap clubs one by one
	members_all = bs.find_all('div', {'class' : re.compile('.*lista-czlonkow.*')})
	
	# for each row in the table
	for members in members_all:
		
		# get club name
		club_name = members.parent.parent.find('div', {'class' : re.compile('.*klub-nazwa.*')}).h2.text
		
		# get club members
		club_members = [' '.join(member.text.split()) for member in 
		members.find_all(lambda tag: tag.name == 'div' and not tag.attrs)]
		
		# compose a dataframe
		df_club = pd.DataFrame(club_members)
		df_club.columns = ['name']
		df_club['club'] = club_name
		
		df_total = pd.concat([df_total, df_club], axis = 0)
		
	return(df_total)
	
def scrap_single_voting(voting_url):
	'''
	function that scraps single voting page given URL
	
	returns dataframe with names of MPs and the votes casted in a given voting
	
	'''
	bs = get_url_content(voting_url)
	senators_raw = bs.find_all('div',{'class' : 'senator'})
	# create list of lists in the form of [[MP, vote_casted], ...]
	senators = [[tag.text.strip('\t\n ') for tag in senator.findChildren()] for senator in senators_raw]
	df = pd.DataFrame(senators)
	df.columns = ["Senator","Vote"]
	
	return(df)


def scrap_day_of_session(session_day_url):
	'''
	function that scrapes the session given the URL
	returns a dataframe with the title, dates and info 
	about the votings that took place in a given day of session
	'''
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
		
		# skip every second "row" since its actually part of the same row (possibly can optimize this)
		votings_extracted = [[vote[i] for i in [0,1,-1]] for k,vote in enumerate(votings_rows) if k%2==0]
		
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
					
		# compose the final frame
		df = pd.DataFrame(votings)
		df.columns = ["No. of voting","Title","Subscript","Link","voting_id"]
		df["Session"] = session_title
		df["Dates"] = session_dates
		return(df)
	else:
		return(False)

# scrap Senate sessisons for dates, linkts to votings and votings' titles
######## info for the URL creation
session_min = 10
session_max = 556
########

######## for printing the progress
to_scrap = session_max - session_min
scrapped = 0
########

#### the input file with links
out_csv = 'output/sessions.csv'
####
print(f'Total sessions to scrap:{to_scrap}')

############## loop calling the  crap_day_of_session function ##########################
for counter,session_id in enumerate(range(session_min,session_max+1)):
	try:	
		if limit_me and scrapped >= 100:
				break	
		print(f'************* Session {counter} of {to_scrap}. Current session id:{session_id}')
		print(f'No. of total scrapped pages: {scrapped}')
		
		day_no = 1
		session_day_url = f"https://www.senat.gov.pl/prace/posiedzenia/przebieg,{session_id},{day_no},glosowania.html"
		
		
		while isinstance(scrap_day_of_session(session_day_url),pd.DataFrame):
			# calling the appropriate function and writing results to csv in chunks
			if limit_me and scrapped >= 100:
				break
			if scrapped == 0:
				df = scrap_day_of_session(session_day_url)
				df.to_csv(out_csv,index=False,header=True)
				day_no += 1
				scrapped += df.shape[0]
				
			else:
				df = scrap_day_of_session(session_day_url)
				df.to_csv(out_csv, index=False, header=False, mode='a')
				day_no += 1
				scrapped += df.shape[0]
			session_day_url = f"https://www.senat.gov.pl/prace/posiedzenia/przebieg,{session_id},{day_no},glosowania.html"
			
		
		if limit_me and scrapped >= 100:
			break
	except HTTPError:
			with open('output/log_unscrapped_sessions.txt', 'a') as f:
				f.write(f', {session_id}')
			print(f'HTTPError for session_id: {session_id}\n Moving on!')
			continue
			
print('Done with sessions!\n')


# get saved links to votings and scrap every voting age by calling the scrap_single_voting function

voting_links = pd.read_csv('output/sessions.csv' , usecols = ['Link','voting_id'])
total_votings = voting_links.shape[0]
counter = 0 

for voting_url, vote_id in zip(voting_links.Link, voting_links.voting_id):
	print(f'scraping vote {counter} out of {total_votings}')
	try:
		
		# calling the appropriate function and writing results to csv in chunks
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

# get party affiliation for all considered terms ###########
possible_terms = [8,9,10]
df_all_terms = pd.DataFrame()
for i,term in enumerate(possible_terms):
	
	try:
		# calling the appropriate function and writing results to csv in chunks
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

