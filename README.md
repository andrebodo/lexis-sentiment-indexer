# Nexis Uni Scraper
This repo contains several scripts to be executed in sequence to download, proceesss and build sentiment indicies based on search results obtained from Nexis Uni.

## Scraping
Scraping Nexis Uni is unreliable due to the excessive usage of JavaScript. This creates issues with loading times and confirming events, which generally can be dealt with selenium waits. Despite this, there are a number of ways that the scraper can fail which cannot be avoided by waits alone. An attempt is made to improve reliability for scraping large datasets by making several attempts. 
