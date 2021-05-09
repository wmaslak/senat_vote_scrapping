# -*- coding: utf-8 -*-
import scrapy
import pandas as pd
from csv import reader
from scrapy.exceptions import CloseSpider


################### scrap senate sessions #########################
class Session(scrapy.Item):
    voting_number = scrapy.Field()
    voting_title = scrapy.Field()
    subscript = scrapy.Field()
    link = scrapy.Field()
    voting_id = scrapy.Field()
    session_title = scrapy.Field()
    dates = scrapy.Field()
   

class VotingLinksSpider(scrapy.Spider):
	
	name = 'sessions'
	
	################ set the limit boolean here ###############
	
	counter = 0
	limiter = True
	
	
     # function that returns the request for apropriately constructed link
	def start_requests(self):
		session_min = 10
		#session_max = 25
		session_max = 556
		domain = 'https://www.senat.gov.pl/'
		for session_id in range(session_min,session_max+1):
			for day_no in range(1,7):
				yield scrapy.Request(url=domain+f'prace/posiedzenia/przebieg,{session_id},{day_no},glosowania.html',callback = self.parse)
    		
    
	


	def parse(self, response):
		
		if self.counter >= 100 and self.limiter:
				print("\n\n########## END FOR TODAY, LIMIT EXCEEDED :) ##########\n\n")
				raise CloseSpider('limit exceeded')
		s = Session()
		# title
		title_raw = response.xpath("//div[@class='meeting-title']//text()")
		title_split = sum([t.split() for t in title_raw.getall()],[])
		title_of_session = ' '.join(title_split)
		# dates
		dates_raw = response.xpath("//div[@class='view-element__date']//text()") 
		dates_split = sum([t.split() for t in dates_raw.getall()],[])
		dates = ' '.join(dates_split)
		### votings table
		voting_tab = response.xpath("//div[@class='table-content']//div[@class='row']")
		# row in the table
		votings_rows = []
		# selected info from the row
		for i,r in enumerate(voting_tab):
			votings_rows.append(r.xpath(".//div"))#.getall())
		
		votings_extracted = [[vote[i] for i in [0,1,-1]] for k,vote in enumerate(votings_rows) if k%2==0]
		
		# write to the Session object fields
		for vote in votings_extracted:
			
			no_of_voting = vote[0].xpath(".//text()").get().strip()
			s['voting_number'] = no_of_voting
			
			title = vote[1].xpath("./child::node()")[1].xpath(".//text()").get().strip()
			s['voting_title'] = title
			#print(f'title: {vote[1].xpath("./child::node()")[1].xpath(".//text()").get().strip()}') 
			
			subscript = vote[1].xpath("./p/i/text()").get() if vote[1].xpath("./p") else 'NA' 
			s['subscript'] = subscript
			#print(f'subscript: {subscript}')
			
			link = vote[2].xpath("./a/@href").get() 
			s['link'] = link
			#print(f'link: {link}')
			
			voting_id = link[link.find(',')+1:link.find('.html')]
			s['voting_id'] = voting_id
		
			s['session_title'] = title_of_session
			s['dates'] = dates
			self.counter += 1
			yield s
			

