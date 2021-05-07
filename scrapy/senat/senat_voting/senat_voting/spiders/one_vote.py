import scrapy
import pandas as pd
from csv import reader
from scrapy.exceptions import CloseSpider

############### scrap single voting #########################################################################
class Senator(scrapy.Item):
	name = scrapy.Field()
	vote = scrapy.Field()
	voting_id = scrapy.Field()

class SingleVotingSpider(scrapy.Spider):
	
	name = 'one_vote'
	
	counter = 0
	################ set limiter to False to perform full scraping
	limiter = True
	###################################################
	
	sessions = pd.read_csv('sessions.csv')
	
	start_urls = [u for u in sessions['link']]


	def parse(self, response):
		
				
		link = response.url
		voting_id = link[link.find(',')+1:link.find('.html')]
		s = Senator()
		senators_raw = response.xpath("//div[@class = 'senator']")
		#print(f'senators raw : {senators_raw[0].xpath("./child::node()/text()")}\n')
		for i,senator_raw in enumerate(senators_raw):
			if self.counter >= 100 and self.limiter:
				print("\n\n########## END FOR TODAY, LIMIT EXCEEDED :) ##########\n\n")
				raise CloseSpider('limit exceeded')
				
			senator = senator_raw.xpath("./child::node()/text()")
			s['name'] = senator[0].get().strip()
			s['vote'] = senator[1].get().strip()
			#print(f"******************* {i} ***********************\n{senator}")
			s['voting_id'] = voting_id
			self.counter += 1
			yield s
		

