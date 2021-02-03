# coding=utf-8

'''
TODO:
- sample test that each title looked up on GS will result the correct article
    - if doesn't work add in date to search conditions
- after that, scrape the abstract and fill csv
- ensure that scaping can be done efficiently, but will not be blocked by GS later on.
'''
import csv

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
import time
import re
import pickle
from fake_useragent import UserAgent
import proxies
import os


global driver
gs_urls = ["https://scholar.google.com/scholar?hl=en", "https://scholar.google.com/scholarf"]
# TODO: LANGUAGE may be marked as NA if search results not fitting...
# LOAD PROXIES CSV?
proxies_old = pd.read_csv('data/proxies.csv', header=0)
proxies_new = pd.read_csv('data/proxies_new.csv', header=0) # update daily or when proxies.csv is low.
proxies = pd.concat([proxies_old, proxies_new]).drop_duplicates().reset_index(drop=True)
# consolidate proxies new with proxies
num_proxies = proxies.shape[0]

print('--total of', num_proxies, 'proxies.--')
print(proxies.head(5), '...')

# LOAD PUBLICATIONS DATA (pubs_urap.csv)
dtypes = {'abstract': str, 'articleID': str, 'AU1': str,
          'AU2': str, 'AU3': str, 'AU4': str, 'AU5': str,
          'AU6': str, 'AU7': str, 'year': str, 'date': str,
          'pages': str, 'journal   ': str, 'Title': str}

pubs = pd.read_csv("data/pubs_urap.csv", dtype=dtypes, index_col=0, na_values=[''], skip_blank_lines=True)

# removes rows from footer of csv for more efficient parsing, removed all rows with no articleID
null_filter = ~pubs['articleID'].isnull().values
pubs_clean = pubs.loc[null_filter, :]


# print(pubs_clean)


def driver_setup():
    #### CHROME DRIVER ####
    ### Proxy
    proxy_idx = np.random.randint(0, num_proxies)
    random_proxy = str(proxies.loc[proxy_idx, 'ip']) + ":" + str(proxies.loc[proxy_idx, 'port'])

    print("proxy:", random_proxy)

    ### Chrome Options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--incognito')
    chrome_options.add_argument('--disable-dev-shm-usage')

    ua = UserAgent()
    userAgent = ua.chrome
    print('user agent:', userAgent)
    chrome_options.add_argument(f'user-agent={userAgent}')
    chrome_options.add_argument('--proxy-server=%s' % random_proxy)

    ## dirs
    chromedriver_path = "chromedriver/chromedriver88"
    prefs = {"download.default_directory": "articles/"}

    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation', "disable-popup-blocking"])

    driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    driver.set_window_size(1200, 900)

    # list cookie packages
    packages = os.listdir('packages')
    cookie_pkg = 'cookies_' + random_proxy + '.pkg'
    #print(cookie_pkg, packages)
    if cookie_pkg in packages:
        # load package
        print("proxy worked before...")
        cookies = pickle.load(open('packages/' + cookie_pkg, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)


    return proxy_idx, random_proxy, driver


# random check
# np.permuatation(0, pubs_clean.shape()[1], 100)
# get sample
# use browser to search up
# get year
# compare scraped year with data year
# ensure they are all right.

# search bar and search button setup
# search_bar = browser.find_element_by_xpath('//*[@id="gs_hdr_tsi"]')
# search_button = browser.find_element_by_xpath('//*[@id="gs_hdr_tsb"]')

# time.sleep(1)

def search(driver, query, p_idx, proxies, bar=None, button=None, year=''):
    global captcha_done
    url = gs_urls[0] + '&as_sdt=0%2C5&q=' + query + '&btnG='
    try:
        driver.get(url)
    except Exception as e:
        print("FAILED TO CONNECT. Remove proxy")
        proxies.drop(index=p_idx, inplace=True)
        # maybe delete proxy cookies?
        # rewrite data/proxies.csv
        # clear old file
        os.remove('data/proxies.csv')

        proxies.to_csv('data/proxies.csv', index=False)
        driver.quit()
        quit()

    timeout = 60

    print('loading...')
    try:
        reload_present = EC.presence_of_element_located((By.XPATH, '//*[@id="reload-button"]'))
        element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="gs_hdr_lgo"]'))
        # sorry_present = EC.presence_of_element_located(()) # case when google says "sorry too many requests from computer or network
        try:
            WebDriverWait(driver, 10).until(element_present)
        except:
            print('reloading...')
            WebDriverWait(driver, 5).until(reload_present)
            driver.find_element_by_xpath('//*[@id="reload-button"]').click()
            WebDriverWait(driver, timeout).until(element_present)

        print("Page loaded.")

    except TimeoutException:
        print("Timed out waiting for page to load.")
        # delete proxy
        proxies.drop(index=p_idx, inplace=True)
        print("proxy deleted.")
        # maybe delete proxy cookies?
        # rewrite data/proxies.csv
        # clear old file
        os.remove('data/proxies.csv')

        print("file rewrite.")
        proxies.to_csv('data/proxies.csv', index=False)
        print("file rewrite complete")
        # if proxies df has less than 10, run proxies.py again!
        if proxies.shape[0] <= 5:
            print("proxies running out, running proxies scraper again.")
            # proxies()
            proxies_old = pd.read_csv('data/proxies.csv', header=0)
            proxies_new = pd.read_csv('data/proxies_new.csv', header=0)
            proxies = pd.concat([proxies_old, proxies_new]).drop_duplicates().reset_index(drop=True)

        driver.quit()
        print('quit driver')
        exit()

    time.sleep(np.random.uniform(1, 2))

    try:
        # no recaptcha needed.
        results = driver.find_elements_by_xpath('//*[@id="gs_res_ccl_mid"]/div')
        # print(results)
        if not results:  # or 'robot' in driver.find_element_by_xpath('//*[@id="gs_captcha_f"]/h1').text:
            print("RECAPTCHA- SOLVE MANUALLY")
            #
            # time.sleep(180)
            time.sleep(np.random.uniform(2, 3))
            WebDriverWait(driver, timeout=60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="gs_captcha_c"]')))
            try:
                driver.find_elements_by_xpath('//*[@id="gs_captcha_c"]')
            except:
                driver.refresh()
                WebDriverWait(driver, timeout=100).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="gs_captcha_c"]')))

            try:
                recaptcha = driver.find_element_by_xpath('//*[@id="gs_captcha_c"]')
            except:
                print("recaptcha not loading. remove proxy.")
                proxies.drop(axis=0, index=p_idx, inplace=True)
                # maybe delete proxy cookies?
                # rewrite data/proxies.csv
                # clear old file
                os.remove('data/proxies.csv')

                proxies.to_csv('data/proxies.csv', index=False)
                # if proxies df has less than 10, run proxies.py again!
                if proxies.shape[0] <= 10:
                    print("proxies running out, running proxies scraper again.")
                    # proxies()
                    proxies_old = pd.read_csv('data/proxies.csv', header=0)
                    proxies_new = pd.read_csv('data/proxies_new.csv', header=0)
                    proxies = pd.concat([proxies_old, proxies_new]).drop_duplicates().reset_index(drop=True)

                driver.quit()
                exit()

            '''try:
                need_upgrade = EC.presence_of_element_located((By.XPATH, '/html/body/div/div[3]/p[1]'))
                upgrade = driver.find_element_by_xpath('/html/body/div/div[3]/p[1]')
                if 'upgrade' in upgrade.text:
                    print(upgrade.text)
                    # mark proxy as invalid
                    # delete proxy
                    #proxies.drop(axis=0, index=p_idx, inplace=True)
                    # maybe delete proxy cookies?
                    # rewrite data/proxies.csv
                    # clear old file
                    # os.remove('data/proxies.csv')

                    #proxies.to_csv('data/proxies.csv', index=False)
                    # if proxies df has less than 10, run proxies.py again!
                    #if proxies.shape[0] <= 10:
                    #    proxies()
                    #driver.quit()
                    #exit()
                    print("proxy/user agent does not support upgrade.")'''
            #except Exception:
            print("no errors with recaptcha... proceeding.")
            time.sleep(np.random.uniform(1,2))
            WebDriverWait(driver, timeout=1000).until(
                EC.visibility_of_any_elements_located((By.XPATH, '//*[@id="gs_res_ccl_mid"]/div')))
            # WebDriverWait(driver, timeout=1000, poll_frequency=1).until(EC.invisibility_of_element_located(recaptcha))
            # complete test manually and download cookies.
            captcha_done = True
            print('saving cookies')
            cookies_filename = 'packages/cookies_' + PROXY + '.pkl'
            pickle.dump(driver.get_cookies(), open(cookies_filename, "wb"))

            cookies = pickle.load(open(cookies_filename, "rb"))
            for cookie in cookies:
                driver.add_cookie(cookie)
            results = driver.find_elements_by_xpath('//*[@id="gs_res_ccl_mid"]/div')
            time.sleep(np.random.uniform(1, 2))
            # print('sleep... start new')
            # print(results)
            abstract = find_abstracts(results, proxies)
            return abstract
        else:
            # print(results)
            abstract = find_abstracts(results, proxies)
            return abstract

    except Exception as e:
        if not captcha_done:
            print("probs recaptcha not loading. remove proxy.")
            proxies.drop(index=p_idx, inplace=True)
            # maybe delete proxy cookies?
            # rewrite data/proxies.csv
            # clear old file
            os.remove('data/proxies.csv')

            proxies.to_csv('data/proxies.csv', index=False)
            print(proxies.shape)
            # if proxies df has less than 10, run proxies.py again!
            if proxies.shape[0] <= 3:
                print("proxies running out, running proxies scraper again.")
                # proxies()
                proxies_old = pd.read_csv('data/proxies.csv', header=0)
                proxies_new = pd.read_csv('data/proxies_new.csv', header=0)
                proxies = pd.concat([proxies_old, proxies_new]).drop_duplicates().reset_index(drop=True)

            driver.quit()
            exit()
        else:
            print("something went wrong :(")
        # results = driver.find_elements_by_xpath('//*[@id="gs_res_ccl_mid"]/div')
        # print(results)


def find_abstracts(res, proxies):
    # TODO:yes
    print('finding abstracts.')

    def find_abstract(article, proxies):
        # click link
        try:
            link = article.find_element_by_xpath('(//*[@id="gs_res_ccl_mid"]/div/div[2]/h3/a |'
                                                 ' //*[@id="gs_res_ccl_mid"]/div/div[2]/h3/*/a )').get_attribute('href')
            print("link:", link)
            driver.get(link)
            time.sleep(np.random.uniform(1, 2))
            driver.refresh()
            time.sleep(np.random.uniform(1, 2))
            try:
                # check for "site can't be reached"
                err = driver.find_elements_by_xpath(
                    "(//*[contains(., 'This site can't be reached')] | //*[contains(., 'ERR_')] )")
                #
                print(err.text)
                # remove proxy
                print("FAILED TO CONNECT. Remove proxy and restart driver.")
                proxies = proxies[proxies['ip'] + ':' + proxies['port'] != PROXY]
                # maybe delete proxy cookies?
                # rewrite data/proxies.csv
                # clear old file
                os.remove('data/proxies.csv')

                proxies.to_csv('data/proxies.csv', index=False)

            except:
                print("page is prob loading?")

            try:
                time.sleep(np.random.uniform(5, 10))
                # search the driver for 'abstract'
                try:
                    driver.switch_to().alert().accept()
                    time.sleep(np.random.uniform(1, 2))
                    # save new cookies package.
                    cookies_filename = 'packages/cookies_' + PROXY + '.pkl'
                    pickle.dump(driver.get_cookies(), open(cookies_filename, "wb"))

                    cookies = pickle.load(open(cookies_filename, "rb"))
                    for cookie in cookies:
                        driver.add_cookie(cookie)

                finally:
                    abs = driver.find_elements_by_xpath("(//*[contains(., 'abstract')] | "
                                                        + "//*[contains(., 'Abstract')] | "
                                                        + "//*[contains(., 'ABSTRACT')] | "
                                                        + "//*[contains(., 'description')] |"
                                                        + "//*[contains(., 'Description')] |"
                                                        + "//*[contains(., 'DESCRIPTION')] )")
                    print("abs found:")
                    if not abs:
                        print(abs)
                        return abs
                    else:
                        return 'NA'
                    # driver.execute_script("window.history.go(-1)")

            except:
                print('abs not found?')
                driver.execute_script("window.history.go(-1)")
                return 'NA'
            # get paragraph if it exists
            # else return 'NA'
        except:
            print("no link provided.")
        return 'NA'

    abstract = ''
    if len(res) == 1:
        print('len 1')
        # one query result.
        # make sure the result matches the year and publication
        # click and find abstract.
        abstract = find_abstract(res[0], proxies)
    elif len(res) == 0:
        print('len 0')
        # no results found.
        # fill csv with NA
        abstract = 'NA'
    else:
        print('len +')
        # multiple results: try to find right one by matching year and publication.
        abstract = find_abstract(res[0], proxies)

    return abstract


# setup_cookies()
proxy_idx, PROXY, driver = driver_setup()
time.sleep(np.random.uniform(2, 3))
abstracts = []
captcha_done = False
for i, row in pubs_clean.loc[:, ['Title', 'articleID']].iterrows():
    #print(row)
    title = row['Title']
    articleID = row['articleID']
    print("TITLE: #", i, "::", title)
    # print(title)
    query = re.sub('\s+', '+', title)
    query = re.sub('[^A-Za-z0-9+\-]', '', query)
    # print(title, query)

    # search_bar, search_button = find_searchfuncs(driver)
    try:
        abstract = search(driver, query, proxy_idx, proxies)
    except:
        abstract = 'NA'
    abstracts.append([abstract, articleID])
    # parse_results()
    i += 1

print(abstracts)
try:
    with open('data/abstracts_test.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['abstract'])
        writer.writeheader()
        for data in abstracts:
            writer.writerow(data)
except IOError:
    print("I/O error")
# time.sleep(np.random.randint(10, 30))
#pubs['abstract'] = abstracts
# on failure/exit
driver.quit()

# start 3-4 ish?
# end 5:30
# total queries per proxy = 406


# start 10 PM
# end ??