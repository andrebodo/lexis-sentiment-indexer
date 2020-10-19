# Nexis Uni Scraper
This repo contains several scripts to be executed in sequence to download, processes and build sentiment indices based on search results obtained from Nexis Uni.

#### Order of Execution:
1. scrape.py
2. process.py
3. article_count_index.py
4. index_b.py

## Scraping
Scraping Nexis Uni is unreliable due to the excessive usage of JavaScript. This creates issues with loading times and confirming events, which generally can be dealt with selenium waits. Despite this, there are a number of ways that the scraper can fail which cannot be avoided by waits alone. An attempt is made to improve reliability for scraping large datasets by making several attempts to scrape the data if there is a failure caught by the program.

The following parameters help define the 'robustness' of scraping:  
1. DRIVER_TIMEOUT: _how long selenium will wait before throwing a TimeoutException, I recommend this is minimum of 60 sec_  
2. MAXIMUM_RETRIES: _how many times the code will re-attempt scraping a particular URL before specifying it as a failure_  
3. DOWNLOAD_TIME: _this controls how long the program will wait for a downloaded file to be found in the download directory before considering the URL a failure_

One way you could estimate maximum retries is to consider the average number of results per URL and specify some additional saftey threshold. I found that when more results are returned from a search, the failure rate is much higher (don't ask me why, Nexis Uni sometimes just fails to load parts of the page). For 2000 results I found 20 was a better number of retries since on several URL's there were 7-8 attempts before all the rows could be scraped.

I have tested the scraper for my specific use case and it achieves my objective well. *I am not supporting this code beyond my personal commits*. I am fully aware that I probably didn't catch ever possible test case for failure. That's fine with me because it gets the job done so I can focus on other things. You are free to take this code and modify it (MIT License terms), but I will not respond to and questions about how the code works beyond what I've written here in the comments and readme. Please cite this codebase and author appropriately if you use it to develop research for an academic paper.

#### Terms and Conditions
Nexis Uni does not allow scraping of their data. This scraper is built for academic purposes. By using this codebase or a modified version of it, you are fully responsible for any and all consequences which may arise from scraping Nexis Uni.

#### Configuring Search & User Settings
Search settings are located in _search\_config.yaml_ and are divided into three sections: _general_, _sources_ and _terms_.

1. General Data
  * _base_url_: The stem of the search url. To get this for a different university, perform a manual Nexis search and copy over the matching pattern.  
  * _start_date_: YYYY/MM/DD format, the first day searching will take place  
  * _end_date_:  YYYY/MM/DD format, the last day searching will take place  
  * _scraper\_freq_: This corresponds to any frequency characters compatible with pandas. This feature is untested for anything but 'M'
2. Sources - a list of source ID's obtained from Nexis Uni's content listing csv available [for download here](https://p.widencdn.net/okffmp/Nexis_Uni_--_Content_Listing_--_July_2020)  
3. Terms - a list of binary search terms (currently no compatibility with NLP search). Each line of terms are joined using the 'or' operator always. If you would like to use the 'and' operator, it needs to be specified as part of a search term. As per YAML formatting, in order to produce a search phrase it is required that double-quotations (to indicate search phrases) are encapsulated by single-quotations so the python yaml module can interpret them correctly.  

Configuring the login information is straightforwards in _credentials.yaml_. The fields probably correspond to your institutions SSO login.  

#### Configuring Your Browser
This script only supports geckodriver.exe, you can download it [here](https://github.com/mozilla/geckodriver) and place the .exe in the same directory as scrape.py

#### More Robust, But Not Perfect...
While most issues with scraping Nexis Uni are tackled in this script, one significant issue is that Nexis Uni sometimes fails to download content, but still downloads a placeholder file. If you monitor the scrape you may see this in the form of a seemingly randomly timed toast message in the bottom left of the window. Nexis Uni says "results will be emailed to you" but will download a placeholder file regardless. Luckily this placeholder is easily identified since its naming convention follows the scraper filename pattern with a .txt extension. In the processing step this issue is the first which is addressed.

## Preprocessing
Given that the scraper downloads files in .rtf format, some pre-processing is required to get the raw text and journal meta-data of the article without all the additional formatting and .rtf metadata. This step is simply accomplished by using a nice piece of software called [DocFrac](http://docfrac.net/wordpress/). After extracting all the .zip files, run DocFrac and patiently wait for things to load up. After reading a bunch of posts on SO, I think the ease of using DocFrac far outweighs any sort of attempt that could be made to programmatically convert .rtf to raw .txt  

## File Processing
In the scraper section titled **More Robust, But Not Perfect** I outline an issue with how Nexis Uni occasionally downloads placeholder files which don't contain actual content. Instead these files are text files with their filenames ending in "deliverynotification.txt". Once these files are detected in _processing.py_, a list of incomplete downloads is generated and printed to console. You can choose to modify the outermost loop of _scrape.py_ such that you re-scrape and re-process these files before going further.   

If you haven't noticed yet Nexis Uni is a far-from-perfect result indexer. A clear example of this can be seen throughout the scraping processing where the 'group duplicates' feature is used. This groups _**some**_ of the results, but a keen eye can notice that this feature is unreliable. In addition to this, the scraper also introduces a source of duplication from overlapping date ranges. It's important to de-duplicate the results properly, which is the final step in the _processing.py_ after the article sections and meta-data have been extracted.

This process of deduplication can take a while because of the way duplicates are detected and prevented. SQLite is not exactly the quickest database solution, but it is highly convenient. The code slows noticeably as more records are written, since first the logic is designed to check if a matching row exists based on specific data fields. This could be a good place to improve speed, but it works fast enough for my particular search and requirements. 

There are peer-reviewed papers in respected finance journals which ignore this crucial step when trying to formulate count-based indices. This boggles my mind as to why they are getting past the peer review process in the first place. If you think that is absurd, there are further mis-applications of statistical methods and data handling which make some of these papers totally un-reproducible. A lot of problems are caused by a reliance on the current backend state of Nexis Uni indexing and NLP software. Its bad enough that Nexis Uni is constantly evolving its indexing process, which makes basic searching a non-trivial aspect of the methodology used to arrive at a final index, so there is a great need to reduce and further sources of error and do our best to make the methodology as reproducible as possible. To help accomplish this, the scraper only performs boolean search and does not consider the 'relevance' of results, an algorithm that Nexis Uni doesn't disclose. There are papers that use this 'relevance' feature to prepare input data, and the resulting indices are published online!

## Indexing
#### Methodology 1 - Article Count
Given the de-duplicated articles which have had their metadata neatly separated as well as their content, it is quite easy to create a monthly article count based sentiment index. This article count is a common way to create a simple sentiment index in academia, _article_count_index.py_ takes care of this, outputting data to a csv file



TODO:
- [ ] include SSO url as a yaml input
- [x] explain how to preprocess
- [x] upload processing.py
- [x] explain processing.py
- [ ] upload article_count_index.py
- [x] explain article_count_index.py
- [ ] upload index_b.py
- [ ] explain index_b.py
