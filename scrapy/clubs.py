import scrapy
import pandas as pd
from csv import reader
from scrapy.exceptions import CloseSpider

############################################## scrap clubs ###
class SenatorClub(scrapy.Item):
	name = scrapy.Field()
	club = scrapy.Field()
	term = scrapy.Field()

				
class SingleVotingSpider(scrapy.Spider):
	
	name = 'clubs'
	
	counter = 0
	################ set limiter to False to perform full scraping
	limiter = True
	###################################################
	
	
	def start_requests(self):
		for term in [8,9,10]:
			yield scrapy.Request(url = f'https://www.senat.gov.pl/sklad/kluby-i-kolo/?kadencja={term}',
			callback = self.parse)
	
	def parse(self, response):
		s = SenatorClub()
		link = response.url
		print(f'*****************link: {link}')
		term = link[link.find('=')+1:]
		
		# get table fith clubs and members
		members_all = response.xpath("//div[re:test(@class,'.*lista-czlonkow.*')]")
		
		for members in members_all:
			if self.counter >= 100 and self.limiter:
				print("\n\n########## END FOR TODAY, LIMIT EXCEEDED :) ##########\n\n")
				raise CloseSpider('limit exceeded')
			# get club name
			club_name = members.xpath("./parent::*/parent::*//div[re:test(@class,'.*klub-nazwa.*')]/h2/a/text()").get()
			
			# get names of members and write to SenatorClub object fields
			for member in members.xpath(".//div[not(@*)]"):
				
				name = ' '.join(member.xpath("./a/text()").get().split())
				s['name'] = name
				s['club'] = club_name
				s['term'] = term
				self.counter += 1
				yield s


