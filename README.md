# Instructions
I assume a "python3" alias. If you use have different alias, please change it!
## BS
1. Run `python3 BS.py` in the directory containing the script and the 'output' folder
2. Read the message and decide if you want to limit the scraper to 100 pages
* If yes, DON'T insert anything and just press ENTER 
* If no, insert ANY character (e.g 'a') and press ENTER
3. The outputs can be found in the 'output' folder

## Selenium
1. Run `python3 senat.py` in the directory containing the script and the 'output' folder
2. Read the message and decide if you want to limit the scraper to 100 pages
* If yes, DON'T insert anything and just press ENTER 
* If no, insert ANY character (e.g 'a') and press ENTER
3. The outputs can be found in the 'output' folder

WARNING: The program is really slow. To speed up the process I'd recommend to change the scraping limit to a lower number (set value of max_limit in the code )

## Scrapy
WARNING: Perform every step carefully in the given order. I cannot guarantee that the scrapers ill work if any steps are skipped or swapped!

1. Create a new scrapy project
2. Copy the files `sessions.py` and `clubs.py` to the 'spiders' folder in the project directory
3. Run `scrapy crawl sessions -o sessions.csv`
4. Copy the file `one_vote.py` to the spiders folder
5. Run `scrapy crawl one_vote -o votes.csv`
6. Run `scrapy crawl clubs -0 clubs.csv`

Note: The weird step 4. is a result of the fact that scrapy compiles all spiders that are in the project folder and as spider 'one_vote' is fed by the links stored in the sessions.csv file, it causes problems when you try to run the 'sessions' spider first.
