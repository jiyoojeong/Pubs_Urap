# coding=utf-8

'''
TODO:
- sample test that each title looked up on GS will result the correct article
    - if doesn't work add in date to search conditions
- after that, scrape the abstract and fill csv
- ensure that scaping can be done efficiently, but will not be blocked by GS later on.
'''

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
import time
import pickle
from fake_useragent import UserAgent

gs_urls = ["https://scholar.google.com/scholar?hl=en", "https://scholar.google.com/scholarf"]
# LOAD PROXIES CSV?
proxies = pd.read_csv('data/proxies.csv', header=0)
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
'''
# IGNORE +++++
def setup_cookies():
    #### CHROME DRIVER ####
    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_argument('--no-sandbox')
    #chrome_options.add_argument('--headless')
    #chrome_options.add_argument('--incognito')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chromedriver_path = "chromedriver/chromedriver88"

    prefs = {"download.default_directory": "data"}

    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)

    driver.get("https://scholar.google.com/scholar?hl=en")
    time.sleep(10)
    search_bar, search_button = find_searchfuncs(driver)
    search_bar.send_keys("test")
    search_button.click()
    time.sleep(180)
    # complete recaptcha
    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
    driver.quit()
# IGNORE ++++'''


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
    userAgent = ua.random
    print('user agent:', userAgent)
    chrome_options.add_argument(f'user-agent={userAgent}')
    chrome_options.add_argument('--proxy-server=%s' % random_proxy)

    ## dirs
    chromedriver_path = "chromedriver/chromedriver88"
    prefs = {"download.default_directory": "data"}

    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])

    driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    driver.set_window_size(1200, 900)

    url = gs_urls[np.random.randint(0,2)]
    driver.get(url)
    time.sleep(np.random.uniform(3, 5))
    try:
        err = driver.find_element_by_xpath('//*[@id="main-message"]/h1/span')
        if err == 'This site can\'t be reached':
            random_proxy, driver = driver_setup()
    except:
        cookies_file = 'packages/cookies_' + random_proxy + '.pkl'
        try:
            cookies = pickle.load(open(cookies_file, "rb"))
            for cookie in cookies:
                driver.add_cookie(cookie)
        except Exception:
            print("cookie package not set up yet.")

        return random_proxy, driver


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

def search(name, bar, button, year=''):
    bar.clear()
    time.sleep(np.random.uniform(1, 3))
    for letter in name:
        bar.send_keys(letter)
        time.sleep(np.random.uniform(.01, .2))
    time.sleep(np.random.uniform(1, 3))
    button.click()
    time.sleep(np.random.uniform(2, 10))


def parse_results():
    try:
        results = driver.find_elements_by_xpath('//*[@id="gs_res_ccl_mid"]/div')
        time.sleep(np.random.uniform(2, 3))
        print(results)
        if not results or 'robot' in driver.find_element_by_xpath('//*[@id="gs_captcha_f"]/h1').text:
            print("RECAPTCHA-ED.")
            # time.sleep(180)
            WebDriverWait(driver, timeout=1000, poll_frequency=1).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="gs_captcha_c"]')))
            recaptcha = driver.find_element_by_xpath('//*[@id="gs_captcha_c"]')
            print("found captcha")
            WebDriverWait(driver, timeout=1000, poll_frequency=1).until(EC.invisibility_of_element_located(recaptcha))
            driver.quit()
            # complete test manually and download cookies.
            cookies_filename = 'packages/cookies_' + PROXY + '.pkl'
            pickle.dump(driver.get_cookies(), open(cookies_filename, "wb"))

            cookies = pickle.load(open(cookies_filename, "rb"))
            for cookie in cookies:
                driver.add_cookie(cookie)
            results = driver.find_elements_by_xpath('//*[@id="gs_res_ccl_mid"]/div')
            time.sleep(np.random.uniform(2, 4))
    except:
        print("Something went wrong...")
        results = driver.find_elements_by_xpath('//*[@id="gs_res_ccl_mid"]/div')
        # print(results)
        driver.quit()


def find_searchfuncs(driver):
    time.sleep(np.random.randint(2, 3))
    try:
        print("helosir")
        bar = driver.find_element_by_xpath('//*[@id="gs_hdr_tsi"]')
        time.sleep(np.random.randint(2, 3))
        print("hows ur day goin")
        button = driver.find_element_by_xpath('//*[@id="gs_hdr_tsb"]')
        print("GOOD!")
    except:
        print("recaptcha before search bars appear")
        if 'robot' in driver.find_element_by_xpath('//*[@id="gs_captcha_f"]/h1').text:
            # print("RECAPTCHA-ED.")
            # time.sleep(180)
            WebDriverWait(driver, timeout=1000, poll_frequency=1).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="gs_captcha_c"]')))
            recaptcha = driver.find_element_by_xpath('//*[@id="gs_captcha_c"]')
            print("found captcha")
            WebDriverWait(driver, timeout=1000, poll_frequency=1).until(EC.invisibility_of_element_located(recaptcha))
            driver.quit()
            # complete test and download cookies.
            cookies_filename = 'packages/cookies_' + PROXY + '.pkl'
            pickle.dump(driver.get_cookies(), open(cookies_filename, "wb"))

            cookies = pickle.load(open(cookies_filename, "rb"))
            for cookie in cookies:
                driver.add_cookie(cookie)
            results = driver.find_elements_by_xpath('//*[@id="gs_res_ccl_mid"]/div')
            time.sleep(np.random.uniform(2, 4))

            bar = driver.find_element_by_xpath('//*[@id="gs_hdr_tsi"]')
            time.sleep(np.random.randint(2, 3))
            button = driver.find_element_by_xpath('//*[@id="gs_hdr_tsb"]')
    return bar, button


# setup_cookies()
PROXY, driver = driver_setup()
i = 1
for title in pubs_clean['Title']:
    print("TITLE: #", i, "::", title)
    # print(title)
    search_bar, search_button = find_searchfuncs(driver)
    search(title, search_bar, search_button)
    parse_results()
    i += 1

# time.sleep(np.random.randint(10, 30))

# on failure/exit
driver.quit()

# start 5:55ish
# end
