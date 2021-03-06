#!/usr/bin/env python
"""Scraper for Nexis Uni

This scraper is for downloading a large amount of search results from Nexis Uni. Search terms and sources can be
specified in the search_configuration.yaml file. This has been tested for data spanning multiple years with a monthly
download interval.
"""
import os
import yaml
import time
import pandas as pd
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException

__author__ = 'Andre Bodo'
__copyright__ = 'Copyright 2020, Andre Bodo'
__credits__ = ['Andre Bodo']
__license__ = 'MIT'
__version__ = ''
__maintainer__ = 'Andre Bodo'
__email__ = 'bodo1184@mylaurier.ca'
__status__ = 'Development'

# Control variables
DOWNLOAD_TIMEOUT = 300
DRIVER_TIMEOUT = 60
MAXIMUM_RETRIES = 20

# Directories and filepaths needed
base_path = Path(__file__).parent
gecko_path = str(base_path) + '\\geckodriver.exe'
download_path = str(base_path) + '\\data\\raw\\'
Path(download_path).mkdir(parents=True, exist_ok=True)

# Load login credentials from file
with open('credentials_working.yaml') as file:
    credentials = yaml.load(file, Loader=yaml.FullLoader)

# Build scraping urls
with open('search_config.yaml') as file:
    search_conf = yaml.load(file, Loader=yaml.FullLoader)
url_list = []
search_dates = pd.date_range(search_conf['start_date'], search_conf['end_date'], freq=search_conf['scraper_freq'])
search_dates = [x.strftime('%Y-%m-%d') for x in search_dates]
search_dates[0] = search_conf['start_date'].replace('/', '-')  # replace to ensure first date is respected.
search_terms = ' or '.join([t for t in search_conf['terms']])
search_sources = '&source='.join([s for s in search_conf['sources']])
for i in range(len(search_dates) - 1):
    url = search_conf['base_url'] + f"?q={search_terms}" \
                                    f"&collection=news" \
                                    f"&qlang=bool" \
                                    f"&startdate={search_dates[i]}" \
                                    f"&enddate={search_dates[i + 1]}" \
                                    f"&source={search_sources}" \
                                    f"&context=1516831"
    url_list.append(url.replace(' ', '+'))
pd.DataFrame(data=url_list).to_csv('url_data.csv', index=True, header=False, mode='w')


# Function to download one url
def download_url(url, uidx):
    # Setup webdriver
    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2)  # Don't use default dir
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', download_path)
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/x-zip-compressed')
    driver = webdriver.Firefox(firefox_profile=profile, executable_path=gecko_path)
    wait = WebDriverWait(driver, DRIVER_TIMEOUT)

    # Login
    driver.maximize_window()
    driver.get('https://libproxy.wlu.ca/login?url=http://www.nexisuni.com')
    try:
        e = wait.until(EC.presence_of_element_located((By.ID, 'username')))
    except WebDriverException as e:
        print('unable to login, quitting')
        driver.quit()
        quit()

    e.send_keys(credentials['username'])
    e = driver.find_element_by_id('password')
    e.send_keys(credentials['password'])
    e.send_keys(Keys.ENTER)
    time.sleep(5)  # waits for login

    driver.get(url)

    for attempt in range(MAXIMUM_RETRIES):
        try:
            # group similar
            if attempt == 0:
                e = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@data-action='toggleduplicates']")))
                e.click()

            # page count
            wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='box']")))
            e = wait.until(EC.element_to_be_clickable((By.XPATH, "//nav[@class='pagination']/ol/li[6]/a")))
            total_pages = int(e.text)

            n_selected = 0
            page = 1
            batch = 1
            while page <= total_pages:
                # select everything
                wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='box']")))
                driver.find_element_by_xpath("//input[@data-action='selectall']").click()

                # count selected and verify
                n_selected += len(driver.find_elements_by_css_selector("input:checked[data-docid^='urn:']"))
                wait.until(EC.text_to_be_present_in_element((By.XPATH, "//button[@data-action='viewtray']/span[1]"),
                                                            str(n_selected)))

                # download
                if page % 10 == 0 or page == total_pages:
                    filename = f'idx_{uidx}_batch_{batch:d}'

                    if not Path(str(download_path) + filename + '.ZIP').is_file():  # if file D.N.E try downloading
                        # click download button
                        wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='box']")))
                        wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "//button[@class='has_tooltip' and @data-action='downloadopt']"))).click()

                        # basic options
                        wait.until(EC.element_to_be_clickable((By.ID, "Rtf"))).click()
                        driver.find_element_by_id("SeparateFiles").click()

                        # filename
                        driver.find_element_by_id("FileName").clear()
                        driver.find_element_by_id("FileName").send_keys(filename)

                        # formatting options
                        driver.find_element_by_id('tab-FormattingOptions').click()
                        # cover page
                        chk = wait.until(EC.element_to_be_clickable((By.ID, "IncludeCoverPage"))).get_attribute(
                            'checked')
                        if chk == 'true':
                            driver.find_element_by_id("IncludeCoverPage").click()
                        # first & lastname in footer
                        if driver.find_element_by_id("DisplayFirstLastNameEnabled").get_attribute('checked') == 'true':
                            driver.find_element_by_id("DisplayFirstLastNameEnabled").click()
                        # page numbering
                        if driver.find_element_by_id("PageNumberSelected").get_attribute('checked') == 'true':
                            driver.find_element_by_id("PageNumberSelected").click()
                        # embedded reference links
                        if driver.find_element_by_id("EmbeddedReferences").get_attribute('checked') == 'true':
                            driver.find_element_by_id("EmbeddedReferences").click()
                        # bold search terms
                        if driver.find_element_by_id('SearchTermsInBoldTypeEnabled').get_attribute('checked') == 'true':
                            driver.find_element_by_id('SearchTermsInBoldTypeEnabled').click()
                        # italicize terms
                        if driver.find_element_by_id('SearchTermsInItalicTypeEnabled').get_attribute(
                                'checked') == 'true':
                            driver.find_element_by_id('SearchTermsInItalicTypeEnabled').click()
                        # underline search terms
                        if driver.find_element_by_id('SearchTermsUnderlinedEnabled').get_attribute('checked') == 'true':
                            driver.find_element_by_id('SearchTermsUnderlinedEnabled').click()
                        # bold reporter page numbers
                        if driver.find_element_by_id('DisplayPaginationInBoldEnabled').get_attribute(
                                'checked') == 'true':
                            driver.find_element_by_id('DisplayPaginationInBoldEnabled').click()

                        # download
                        driver.execute_script('arguments[0].click();',
                                              driver.find_element_by_xpath("//button[@data-action='download']"))

                        start_time = time.time()
                        while True:
                            if os.path.exists(str(download_path) + filename + '.ZIP'):
                                if not os.path.exists(str(download_path) + filename + '.ZIP.part'):
                                    break
                            time.sleep(2)
                            if time.time() - start_time > DOWNLOAD_TIMEOUT:
                                raise WebDriverException('download timeout')
                        n_selected = 0
                        batch += 1

                    else:  # File exists, so deselect all and reset selection count
                        wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='box']")))
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-action='viewtray']"))).click()
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-action='cancel']"))).click()
                        wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='box']")))
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-action='confirm']"))).click()
                        n_selected = 0
                        batch += 1

                if page == total_pages:
                    driver.quit()
                    return True

                # navigate to next page
                wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='box']")))
                e = driver.find_element_by_xpath("//nav[@class='pagination']/ol/li[@class='current']/span")
                old_page = int(e.text)
                driver.execute_script('arguments[0].click();',
                                      driver.find_element_by_xpath("//nav[@class='pagination']/ol/li[last()]/a"))
                wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='box']")))
                e = driver.find_element_by_xpath("//nav[@class='pagination']/ol/li[@class='current']/span")
                if int(e.text) == (old_page + 1):
                    page += 1
                else:
                    raise WebDriverException('did not navigate to next page')
        except (WebDriverException, ValueError, TypeError) as ex:
            # make sure nothing is selected, this can occur if there is an exception and part of page is selected
            try:
                wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='box']")))
                sel_count = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//button[@data-action='viewtray']/span[1]"))).text
                if sel_count != '' and sel_count is not None:
                    wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='box']")))
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-action='viewtray']"))).click()
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-action='cancel']"))).click()
                    wait.until(EC.invisibility_of_element_located((By.XPATH, "//div[@class='box']")))
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-action='confirm']"))).click()
                    n_selected = 0
            except WebDriverException as wex_inner:
                pass
            print(f'[{uidx}] <{str(ex).strip()}>')
            driver.get(url)
            time.sleep(2.5)
        else:  # If there were no exceptions this block gets executed
            driver.quit()
            return True
    else:
        driver.quit()
        print(f'[{uidx}] max retry failed: aborting url')
        return False


failed_urls = []
failed_url_idx = []
uidx = 0
while uidx < len(url_list):
    url = url_list[uidx]
    print(f'processing: [{uidx}] of [{len(url_list) - 1}]: ')
    res = download_url(url, uidx)
    if not res:
        failed_urls = failed_urls.append(url)
        failed_url_idx = failed_url_idx.append(uidx)
        print('...failed.')
    else:
        print('...success.')
    uidx += 1
print('Failed urls:')
print([str(f) + '\n' for f in failed_urls])
print(failed_url_idx)