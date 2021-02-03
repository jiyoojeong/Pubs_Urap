
from fake_useragent import UserAgent
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import csv
import os
import pandas as pd


# SET UP PROXIES @source: https://medium.com/ml-book/multiple-proxy-servers-in-selenium-web-driver-python-4e856136199d
def proxy_setup():
    #### AGENT SETUP ####
    ua = UserAgent(use_cache_server=False)

    #### PROXY SETUP ####
    proxies = []  # Will contain proxies [ip, port]

    # Retrieve latest proxies
    proxies_req = Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    # Save proxies in the array
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
            'ip': row.find_all('td')[0].string,
            'port': row.find_all('td')[1].string,
            'country': row.find_all('td')[3].string,
            'anon': row.find_all('td')[4].string,
        })

    print(proxies)
    proxies = pd.DataFrame(proxies)
    print(proxies)
    proxies_elite = proxies.loc[proxies['anon'] == 'elite proxy' and proxies['country'] == 'US', ['ip', 'port']]
    print(proxies_elite)
    # Retrieve a random index proxy (we need the index to delete it if not working)

    proxy_index = 0
    proxy = proxies_elite.loc[proxy_index, :]
    # print(proxy)
    total_num = proxies_elite.shape[0]
    print("total elites:", total_num)
    proxies_elite['valid'] = True
    for n in range(1, total_num):
        req = Request('http://icanhazip.com')
        req.set_proxy(proxy['ip'] + ':' + proxy['port'], 'http')

        # Every 10 requests, generate a new proxy
        # if n % 10 == 0:

        # Make the call
        try:
            my_ip = urlopen(req).read().decode('utf8')
            if len(my_ip) > 20:
                print('Proxy ' + proxy['ip'] + ':' + proxy['port'] + ' deleted.')
                proxies_elite.loc[n - 1, 'valid'] = False
                raise IOError
            print('#' + str(n) + ': ' + my_ip)
        except:  # If error, delete this proxy and find another one
            # proxies_elite.drop(axis=0, index=proxy_index, inplace=True)
            print('Proxy ' + proxy['ip'] + ':' + proxy['port'] + ' deleted.')
            proxies_elite.loc[n - 1, 'valid'] = False

        proxy = proxies_elite.iloc[n, :]

    # print(proxies)

    csv_file = "data/proxies_new.csv"
    # clear old file
    try:
        os.remove(csv_file)
    except:
        print("proxies_new not made yet.")
    # write new dataframe to csv
    valid_proxies = proxies_elite.loc[proxies_elite['valid'], ['ip', 'port']]
    valid_proxies.to_csv(csv_file, index=False)
    '''
    try:
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['ip', 'port'])
            writer.writeheader()
            for data in proxies:
                writer.writerow(data)
    except IOError:
        print("I/O error")
    '''


if __name__ == "__main__":
    print('running proxies')
    proxy_setup()
    print('complete, updated in proxies_new.csv')