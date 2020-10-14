# Nexis Uni Scraper
This repo contains several scripts to be executed in sequence to download, proceesss and build sentiment indicies based on search results obtained from Nexis Uni.

### Order of Execution:
1. scrape.py
2. process.py
3. index_a.py
4. index_b.py

## Scraping
Scraping Nexis Uni is unreliable due to the excessive usage of JavaScript. This creates issues with loading times and confirming events, which generally can be dealt with selenium waits. Despite this, there are a number of ways that the scraper can fail which cannot be avoided by waits alone. An attempt is made to improve reliability for scraping large datasets by making several attempts to scrape the data if there is a failure caught by the program.

The following parameters help define the 'robustness' of scraping:  
1. DRIVER_TIMEOUT: _how long selenium will wait before throwing a TimeoutException, I recommend this is minimum of 60 sec_  
2. MAXIMUM_RETRIES: _how many times the code will re-attempt scraping a particular URL before specifying it as a failure_  
3. DOWNLOAD_TIME: _this controls how long the program will wait for a downloaded file to be found in the download directory before considering the URL a failure_

One way you could estimate maximum retries is to consider the average number of results per URL and specify some additional saftey threshold. I found that when more results are returned from a search, the failure rate is much higher (don't ask me why, Nexis Uni sometimes just fails to load parts of the page). For 2000 results I found 20 was a better number of retries since on several URL's there were 7-8 attempts before all the rows could be scraped.

I have tested the scraper for my specific use case and it achieves my objective well. *I am not supporting this code beyond my personal commits*. I am fully aware that I probably didn't catch ever possible test case for failure. That's fine with me because it gets the job done so I can focus on other things. You are free to take this code and modify it (MIT License terms), but I will not respond to and questions about how the code works beyond what I've layed out here in the comments and readme. Please cite this codebase and author appropriately if you use it to develop research for an academic paper.

### Terms and Conditions
Nexis Uni does not allow scraping of their data. This scraper is built for academic purposes. By using this codebase or a modified version of it, you are fully responsible for any and all consequences which may arise from scraping Nexis Uni.

### Configuring Search & User Settings
Search settings are located in _search\_config.yaml_ and are divided into three sections: _general_, _sources_ and _terms_.

1. General Data  
  * _base_url_: The stem of the search url. To get this for a different university, perform a manual Nexis search and copy over the matching pattern.  
  * _start_date_: YYYY/MM/DD format, the first day searching will take place  
  * _end_date_:  YYYY/MM/DD format, the last day searching will take place  
  * _scraper\_freq_: This corresponds to any frequency characters compatible with pandas. This feature is untested for anything but 'M'  
2. Sources - a list of soruce ID's obtained from Nexi Uni's content listing csv available [for download here](https://p.widencdn.net/okffmp/Nexis_Uni_--_Content_Listing_--_July_2020)  
3. Terms - a list of binary search terms (currently no compatibility with NLP search). Each line of terms are joined using the 'or' operator always. If you would like to use the 'and' operator, it needs to be specified as part of a search term. As per YAML formatting, in order to produce a search phrase it is required that double-quotations (to indicate search phrases) are encapuslated by single-quotations so the python yaml module can interpret them correctly.  

Configuring the login information is straightforwards in _credentials.yaml_. The fields probably correspond to your institutions SSO login.  
__TODO: include SSO url as an input


## Preprocessing
TODO

## File Processing
TODO

## Indexing

TODO:
* Method 1
* Method 2 
