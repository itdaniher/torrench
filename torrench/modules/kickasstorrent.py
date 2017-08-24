'''
KickassTorrent Module
'''

import sys
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate
import colorama
import time
import webbrowser
import platform
from torrench.utilities.find_url import proxy_list

print("""
#########################
#                       #
#    KickAssTorrents    #                         
#                       #
#########################
""")

'''
Initialisations
'''
colorama.init()
YELLOW = colorama.Fore.YELLOW + colorama.Style.BRIGHT
GREEN = colorama.Fore.GREEN + colorama.Style.BRIGHT
RED = colorama.Fore.RED + colorama.Style.BRIGHT
RESET = colorama.Style.RESET_ALL

OS_WIN = False
master_list = []
mapper = []
index = 0
page_fetch_time = 0
total_fetch_time = 0
torrent_count = 9999

if platform.system() == "Windows":
    OS_WIN = True

'''
Function to fetch 'url' page and prepare soup
It also gives the time taken to fetch url
'''


def http_request(url):
    global page_fetch_time
    try:
        start_time = time.time()
        raw = requests.get(url)
        page_fetch_time = time.time() - start_time
    except requests.exceptions.ConnectionError:
        print("Connection error...")
        return 1
    raw = raw.content
    soup = BeautifulSoup(raw, 'lxml')
    return soup


'''
Function to select appropriate (available) proxy
from proxy list.
If a proxy is unavilable (connectionerror),
next proxy is tried
'''


def cycle_proxies(proxy_list):
    i = 0
    url = proxy_list[i]
    print(">>> Trying %s" % (YELLOW + url + RESET))
    res = http_request(url)
    if res == 1:
        i += 1
        if i >= len(proxy_list):
            print("No appropriate proxies found.")
            sys.exit("Exiting!")
        url = proxy_list[i]
        print("\n>>> Trying %s" % (YELLOW + url + RESET))
        http_request(url)
    return url


'''
Function to obtain proxy list
'''


def proxy_select():
    print("Obtaining proxies...")
    proxyList = proxy_list('kat')
    return proxyList


'''
Function to obtain results for given user input
It includes fetching pages (if -p is provided)
variables used:
-- torrent_count :: to count number of torrents fetched from a page.
If 50 torrents are fetched (means 2 pages) and (-p) argument is 4,
Then fetching process stops at 2, and no further pages are fetched.
This is what torrent_count is used for (here)
   
-- title :: the title given by user
-- page_limit :: Value of (-p) argument
This function calls the fetch_results() to obtain results and are stored in 'output'
'''


def soup_output(url, title, page_limit):
    global torrent_count
    for p in range(page_limit):
        if torrent_count < 30:
            break
        search = "usearch/%s/%d/" % (title, p + 1)
        if page_limit > 1:
            print("Fetching from page: %d" % (p + 1))
        else:
            print("Fetching results...")
        soup = http_request(url + search)
        output = fetch_results(soup)
    return output


'''
Fetch results for given input (soup)
soup is from get_results()
Following data is fetched:
- name
- uploader name
- uploader status (verified or not)
--- Yellow=Verified uploader
- Comments (Number)
- Category
- Seeds
- Leeches
- Date (of upload)
- Size
- magnetic link*
All this result is displayed in tabular form (tabulate)

* Not displayed in table, but later
'''


def fetch_results(soup):

    mylist = []
    global torrent_count
    torrent_count = 0
    content = soup.find('table', class_='data')
    try:
        data = content.find_all('tr', class_='odd')
    except AttributeError as e:
        print("Proxy not working!! (Did you update the config.ini file?)")
        print("I have not been able to find any reliable KAT proxy site.")
        print("If you know of some working proxy, you can edit the config.ini file (KAT_URL) with that proxy.")
        print("And hope it works (If it does, let me know?).")
        print("Alternatively, use TPB. Its pretty reliable!\nExiting!")
        sys.exit(2)
    if data == None:
        print("\nNo results found for given input!\n")
        sys.exit("Exiting!")

    for i in data:
        name = i.find('a', class_='cellMainLink').string
        if name == None:
            name = i.find('a', class_='cellMainLink').get_text().split("[[")[0]
        if OS_WIN:
            try:
                name = name.encode('ascii', 'replace').decode()  # Handling Unicode characters in windows.
            except AttributeError:
                pass

        torrent_link = i.find('a', class_='cellMainLink')['href']
        uploader_name = i.find('span', class_='lightgrey').get_text().split(" ")[-4]
        category = i.find('span', class_='lightgrey').get_text().split(" ")[-2]
        verified_uploader = i.find('a', {'title': 'Verified Torrent'})
        if verified_uploader != None:
            uploader_name = YELLOW + uploader_name + RESET
            verified = True
            comment_count = i.find('a', class_='icommentjs').get_text()
        if comment_count == '':
            comment_count = 0
        misc_details = i.find_all('td', class_='center')
        size = misc_details[0].string
        date_added = misc_details[1].string
        seeds = GREEN + misc_details[2].string + RESET
        leeches = RED + misc_details[3].string + RESET
        magnet = i.find('a', {'title': 'Torrent magnet link'})['href']

        global index
        index += 1
        torrent_count += 1

        # Storing each row result in mylist
        mylist = [category, name, '--' + str(index) + '--', uploader_name, size, date_added, seeds, leeches, comment_count]
        # Further, appending mylist to a masterlist. This masterlist stores the required result
        master_list.append(mylist)

        # Array to map torrent name with corresponding link and magnet-link (Used in get_torrent())
        mapper.insert(index, (name, magnet, torrent_link))

    global page_fetch_time
    global total_fetch_time
    total_fetch_time += page_fetch_time
    print("Torrents: %d [in %.2f sec] \n" % (torrent_count, page_fetch_time))
    result = tabulate(master_list, headers=['CATEG', 'NAME', 'INDEX', 'UPLOADER', 'SIZE', 'DATE', 'S', 'L', 'C'], tablefmt='grid')
    return result


'''
Function called after output table is displayed. 
Displays text and following info:
- Total torrents fetched (index)
- Time taken to fetch all torrents (total_fetch_time)
- Total pages fetched (exact_no_of_pages)
'''


def after_output_text():
    global total_fetch_time
    global index
    exact_no_of_pages = index // 30
    has_extra_pages = index % 30
    if has_extra_pages > 0:
        exact_no_of_pages += 1
    print("\nTotal %d torrents [%d pages]" % (index, exact_no_of_pages))
    print("Total time: %.2f sec" % (total_fetch_time))
    print("\nFurther, torrent can be downloaded using magnetic link\nOR\nTorrent's upstream link can be obtained to be opened in web browser.")
    print("\nEnter torrent's index value (Maximum one index)")
    return


'''
Each torrentis associated to an index.
Torrent is selected using the index value.
Operations:
- Print magnetic link, upstream link and option to load torrent to torrent-client

As of now, the magnetic link is opened in browser, *assuming* it automatically opens
the link in default torrent client
'''
'''
TODO: Load torrent directly to torrent client. If multiple clients are present, ask user.
'''


def get_torrent(url):
    index = 999
    while(index != 0):
        try:
            index = int(input("\n(0=exit)\nindex > "))
            if index == 0:
                print("\nBye!\n")
                break
            selected_torrent, req_magnetic_link, torrent_link = mapper[index]
        except ValueError:
            print("\nBad Input!")
            continue
        except IndexError:
            print("\nBad Input!")
            continue

        selected_torrent = map_name_index[str(index)]
        req_magnetic_link = map_magnet_index[str(index)]
        req_torr_link = map_torrlink_index[str(index)]
        print("Selected index [%d] - %s\n" % (index, selected_torrent))
        print("Upstream Link: %s \n" % (YELLOW + url + req_torr_link + RESET))
        print("Magnetic Link: %s \n" % (RED + req_magnetic_link + RESET))
        option = input("Load magnetic link to client? [y/n]:")
        if option == 'y' or option == 'Y':
            try:
                webbrowser.open_new_tab(req_magnetic_link)
            except Exception as e:
                print(e)
                continue
        else:
            continue


'''
Execution begins here
- Obtain proxy list
- Select proxy to use
- Fetch results for 'title' and 'page_limit'
- Obtain specific torrent
'''


def main(title, page_limit):
    i = 0
    try:
        print("Note: KAT can be slower at times, and take longer time than usual to fetch results.\n\n")
        proxy_list = proxy_select()
        url = cycle_proxies(proxy_list)
        output = soup_output(url, title, page_limit)
        print("\nS=SEEDS; L=LEECHES; C=COMMENTS; " + YELLOW + "YELLOW UPLOADERS " + RESET + "are Verified Uploaders")
        print(output)
        after_output_text()
        get_torrent(url)
    except KeyboardInterrupt:
        print("\n\nAborted!")


if __name__ == "__main__":
    print("It's a module")
