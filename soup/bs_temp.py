


if input("Insert any character to allow scraping over 100 pages. Press enter to limit scraping: "):
    limit_me = False
else:
    limit_me = True
#limit_me = False



n0 = 1
nMax = 10650

#voting_id = 10100
#voting_url = f'https://www.senat.gov.pl/prace/posiedzenia/glosowanie-drukuj,{voting_id}.html'
#session_day_url =

session_min = 10
session_max = 556
#day_no = 2
#session_id = 502
#url = f"https://www.senat.gov.pl/prace/posiedzenia/przebieg,{session_id},{day_no},glosowania.html"
#print(url)

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

def scrap_single_voting(voting_url):

	bs = get_url_content(voting_url)
	senators_raw = bs.find_all('div',{'class' : 'senator'})
	senators = [[tag.text.strip('\t\n ') for tag in senator.findChildren()] for senator in senators_raw]
	df = pd.DataFrame(senators)
	df.columns = ["Senator","Vote"]
	
	return(df)

		
		

#get saved links to votings
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

