'''
ThePirateBay Module
'''

import requests
from bs4 import BeautifulSoup
from tabulate import tabulate
import colorama
import time
import webbrowser
import sys
import platform
from torrench.utilities.find_url import proxy_list
from torrench.modules.tpb_details import get_details

print("""
######################
#                    #
#    ThePirateBay    #
#                    #
######################
""")


'''
Initialisations
'''
colorama.init()
YELLOW = colorama.Fore.YELLOW + colorama.Style.BRIGHT
GREEN = colorama.Fore.GREEN + colorama.Style.BRIGHT
MAGENTA = colorama.Fore.MAGENTA + colorama.Style.BRIGHT
RED = colorama.Fore.RED + colorama.Style.BRIGHT
RESET = colorama.Style.RESET_ALL

OS_WIN = False
index = 0
page_fetch_time = 0
total_fetch_time = 0
torrent_count = 9999
master_list = []
mapper = []

if platform.system() == "Windows":
    OS_WIN = True

'''
Function to obtain proxy list
'''


def proxy_select():
    print("Obtaining proxies...")
    proxyList = proxy_list('tpb')
    return proxyList


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
        if i > len(proxy_list):
            print("No appropriate proxies found.")
            sys.exit("Exiting!")
        url = proxy_list[i]
        print("\n>>> Trying %s" % (YELLOW + url + RESET))
        http_request(url)
    return url


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


def get_results(url, title, page_limit):
    global torrent_count
    for p in range(page_limit):
        if torrent_count < 30:
            break
        search = "/search/%s/%d/99/0" % (title, p)
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
- uploader status (VIP/Trusted/General)
--- Green=VIP; Magenta=Trusted; White=General
- Comments (Number)
- Category:Sub-category
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
    website_url = soup.find('img', id='TPBlogo')['src'].split('/')[2]
    content = soup.find('table', id="searchResult")
    if content == None:
        print("\nNo results found for given input!")
        sys.exit(2)

    data = content.find_all('tr')
    for i in data[1:]:
        name = i.find('a', class_='detLink').string
        uploader = i.find('font', class_="detDesc").a

        if name == None:
            name = i.find('a', class_='detLink')['title'].split(" ")[2:]
            name = " ".join(str(x) for x in name)

        if uploader == None:
            uploader = i.find('font', class_="detDesc").i.string
        else:
            uploader = uploader.string

        if OS_WIN:
            name = name.encode('ascii', 'replace').decode()  # Handling Unicode characters in windows.

        comments = i.find('img', {'src': '//%s/static/img/icon_comment.gif' % (website_url)})
        if comments != None:
            comment = comments['alt'].split(" ")[-2]  # Total number of comments
        else:
            comment = "0"

        is_vip = i.find('img', {'title': "VIP"})
        is_trusted = i.find('img', {'title': 'Trusted'})
        if(is_vip != None):
            name = GREEN + name + RESET
            uploader = GREEN + uploader + RESET
        elif(is_trusted != None):
            name = MAGENTA + name + RESET
            uploader = MAGENTA + uploader + RESET
        categ = i.find('td', class_="vertTh").find_all('a')[0].string
        sub_categ = i.find('td', class_="vertTh").find_all('a')[1].string
        seeds = i.find_all('td', align="right")[0].string
        leeches = i.find_all('td', align="right")[1].string
        date = i.find('font', class_="detDesc").get_text().split(' ')[1].replace(',', "")
        size = i.find('font', class_="detDesc").get_text().split(' ')[3].replace(',', "")
        torr_id = i.find('a', {'class': 'detLink'})["href"].split('/')[2]
        link = "https://%s/torrent/%s" % (website_url, torr_id)
        magnet = i.find_all('a', {'title': 'Download this torrent using magnet'})[0]['href']

        global index
        index += 1
        torrent_count += 1
        # Storing each row result in mylist
        mylist = [categ + " > " + sub_categ, name, "--" + str(index) + "--", uploader, size, seeds, leeches, date, comment]
        # Further, appending mylist to a masterlist. This masterlist stores the required result
        master_list.append(mylist)

        # Array to map torrent name with corresponding link and magnet-link (Used in get_torrent())
        mapper.insert(index, (name, magnet, link))

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
    print("\nFurther, a torrent's details can be fetched (Description, comments, download(Magnetic) Link, etc.)")
    print("Enter torrent's index value to fetch details (Maximum one index)\n")
    return


'''
Each torrentis associated to an index.
Torrent is selected using the index value.
Options:
- Print magnetic link (and load it to torrent-client)
- Fetch torrent details and store it to hard-drive

Fetching torrent details:
Torrent details are stored in a dynamically generated HTML file.
Details include:
- All torrent basic details (name, date, seeds, leeches, size, uploader, torrent-hash, category...)
- Torrent description
- Torrent comments
details are fetched from modules.tpb_details module
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
                print("\nBye!")
                sys.exit(2)
            selected_torrent, req_magnetic_link, torrent_link = mapper[index]
        except ValueError:
            print("\nBad Input!")
            continue
        except IndexError:
            print("\nBad Input!")
            continue

        print("Selected index [%d] - %s\n" % (index, selected_torrent))
        option2 = input("1. Print magnetic link [m]\n2. Get torrent details [g]\n\nOption [m/g]: ")
        if option2 == 'm' or option2 == 'g':
            if option2 == 'm':
                print("\nMagnetic link - %s" % (RED + req_magnetic_link + RESET))
                uip = input("\nLoad to torrent client? [y/n]: ")
                if uip == 'y' or uip == 'Y':
                    try:
                        webbrowser.open_new_tab(req_magnetic_link)
                    except Exception as e:
                        print(e)
                        continue
            elif option2 == 'g' or option2 == 'G':
                print("Fetching details for torrent index [%d] : %s" % (index, selected_torrent))
                file_url = get_details(torrent_link, str(index))
                file_url = YELLOW + file_url + RESET
                print("File URL: " + file_url + "\n")


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
        proxy_list = proxy_select()
        url = cycle_proxies(proxy_list)
        output = get_results(url, title, page_limit)
        print("\nS=SEEDS; L=LEECHES; C=COMMENTS")
        print(output)
        after_output_text()
        get_torrent(url)
    except KeyboardInterrupt:
        print("\n\nAborted!")


if __name__ == "__main__":
    print("It's a module!")
