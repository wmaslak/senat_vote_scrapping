from selenium import webdriver
import time
import getpass
import datetime
import pandas as pd


################ getting limit info from CLI input #############################
if input("Insert any character to allow scraping over 100 pages. Press enter to limit scraping: "):
    limit_me = False
else:
    limit_me = True

max_limit = 100
scraped = 0
########################################

def scrap_single_voting(voting_url):
	'''
	function that scraps names of senators and votes from the voting webpage
	'''
	driver.get(voting_url)
	senators_raw = driver.find_elements_by_xpath("//div[@class = 'senator']")
	senators = [[tag.text.strip('\t\n ') for tag in senator.find_elements_by_xpath("./child::*")] for senator in senators_raw]
	df = pd.DataFrame(senators)
	df.columns = ["Senator","Vote"]
	
	return(df)
	
def scrap_clubs(term_url):
	'''
	function that craps the sessions and links to particular votings
	'''
	driver.get(term_url)
	df_total = pd.DataFrame()
	
	# scrap clubs one by one
	members_all = driver.find_elements_by_xpath("//div[contains(@class,'lista-czlonkow')]")
	
	for members in members_all:
		club_name = members.find_element_by_xpath("./parent::*/parent::*//div[contains(@class,'klub-nazwa')]/h2/a").text
		print(club_name)
		club_members = []
		#print(members.find_elements_by_xpath(".//div[not(@*)]"))
		for member in members.find_elements_by_xpath(".//a[contains(@href,'senator')]"):
				#print(term,'\n')
				#print(member.xpath("./text()").get())
				name = member.get_attribute("innerText")
				club_members.append(name)
		
		#print(club_members)
		df_club = pd.DataFrame(club_members)
		df_club.columns = ['name']
		df_club['club'] = club_name
		
		df_total = pd.concat([df_total, df_club], axis = 0)
		
	return(df_total)





start = time.time()

gecko_path = '/usr/local/bin/geckodriver'
options = webdriver.firefox.options.Options()
options.headless = True
driver = webdriver.Firefox(options = options, executable_path = gecko_path)

####### scrap sessions ##########################

master_df = pd.DataFrame()

session_min = 10
session_max = 556
# iterate over the sessions' links and get the description of session and links to votings
for session_id in range(session_min, session_max+1):
	for day_no in range(1,8):
		if limit_me and scraped >= max_limit:
			break
		try:	
				
			url = f"https://www.senat.gov.pl/prace/posiedzenia/przebieg,{session_id},{day_no},glosowania.html"
			print(f'>>>>>>>>>>> current url: {url}')
			driver.get(url)
			#print(driver.page_source)

			# dates and titles
			title = driver.find_element_by_xpath("//div[@class='meeting-title']").text
			dates = driver.find_element_by_xpath("//div[@class='view-element__date']").text

			# voting links
			try:
				# find the table with votings
				voting_tab = driver.find_elements_by_xpath("//div[@class='table-content']//div[@class='row']")
				# get the list with rows
				votings_rows = []
				for i,r in enumerate(voting_tab):
					votings_rows.append(r.find_elements_by_xpath(".//div"))#.getall())
				
				# from each row extract needed info
				votings_extracted = [[vote[i] for i in [0,1,-1]] for k,vote in enumerate(votings_rows) if k%2==0]

				votings = []
				for vote in votings_extracted:
					if limit_me and scraped >= max_limit:
						break	
					no_of_voting = vote[0].text.strip()

					title = vote[1].find_element_by_xpath("./child::*").text.strip()
					

					subscript = vote[1].find_element_by_xpath("./p/i").text if vote[1].find_element_by_xpath("./p") else 'NA' 


					link = vote[2].find_element_by_xpath("./a").get_attribute('href') 

					voting_id = link[link.find(',')+1:link.find('.html')]
					print(f'voting_id: {voting_id}')
					
					votings.append([no_of_voting,
								title,
								subscript,
								link,
								voting_id])
					scraped += 1
					
				df = pd.DataFrame(votings)
				df.columns = ["No. of voting","Title","Subscript","Link","voting_id"]
				df["Session"] = title
				df["Dates"] = dates
				master_df = pd.concat([master_df,df])
			except:
				print(f'skipping day: {day_no} \nno votings that day')
		except:
			print(f'skipping day: {day_no} at session: {title} \nno such day')
			continue
# write to csv
master_df.to_csv('output/sessions.csv', index = False)

############################### scrap all votes ############################################333
# get links and voting_ids from csv
voting_links = pd.read_csv('output/sessions.csv' , usecols = ['Link','voting_id'])

total_votings = voting_links.shape[0]
counter = 0 
for voting_url, vote_id in zip(voting_links.Link, voting_links.voting_id):
	print(f'scraping vote {counter} out of {total_votings}')
	try:	
		# call the appropriate scraping function and write result in chunks to a csv 
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
		
	except:
		with open('output/log_unscrapped_votes.txt', 'a') as f:
			f.write(f', {voting_url}')
			print(f'HTTPError for voting url: {voting_url}\n Moving on!')
		continue
		
################################## scrap clubs ################################
possible_terms = [8,9,10]
df_all_terms = pd.DataFrame()
for i,term in enumerate(possible_terms):
	
	try:	
		# call the appropriate scraping function and write result in chunks to a csv 
		# construct link on the fly
		term_df = scrap_clubs(f'https://www.senat.gov.pl/sklad/kluby-i-kolo/?kadencja={term}')
		term_df['Term number'] = term
		#print(term_df)
		df_all_terms = pd.concat([df_all_terms,term_df],axis=0)
		if enumerate == 0:
			df_all_terms.to_csv('output/clubs.csv',index=False,header=True)
		else:
			df_all_terms.to_csv('output/clubs.csv',index=False,header=False, mode = 'a')
		
	except:
		print(f'Some problem with term {term}. Moving on!')
		continue


driver.quit()

end = time.time()
print(f'********************** Elapsed time: {end - start} *********************************')
