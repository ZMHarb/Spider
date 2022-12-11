#!/bin/python3

'''
usage:
------
spider.py [url] -l 
spider.py [url] -d -w [FILE]                               
spider.py [url] -s -w [FILE] -t [int]                     
spider.py [url] -a -w [FILE] [FILE] -o [FILE]
spider.py [url] -d -x -w [FILE] -t [int]          
spider.py [url] --all-links 
...
'''

banner = '''

 ██████╗██████╗ ██╗██████╗ ███████╗██████╗   
██╔════╝██╔══██╗██║██╔══██╗██╔════╝██╔══██╗
╚█████╗ ██████╔╝██║██║  ██║█████╗  ██████╔╝
 ╚═══██╗██╔═══╝ ██║██║  ██║██╔══╝  ██╔══██╗
██████╔╝██║     ██║██████╔╝███████╗██║  ██║
╚═════╝ ╚═╝     ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝           version: 1.0

* Websites Crawler Tool
* Created by ZMHarb
* Project https://github.com/ZMHarb/spider.git
-----------------------------------------------
'''

from re import findall
from sys import argv
from time import ctime
from os import getcwd
from urllib import parse
from colorama import Fore
from argparse import ArgumentParser, SUPPRESS, RawTextHelpFormatter
from threading import Thread

import requests

def prepare_list(wordlist, nbr_of_sublist):
    '''
    Function used for giving each thread a wordlist

    :param wordlist: the complete wordlist
    :param nbr_of_sublist: nbr of sublists to create

    '''
    for i in range(0, len(wordlist), nbr_of_sublist):
        yield wordlist[i: i + nbr_of_sublist]

def read_file(file):
    '''
    Function used to read the content of a given file

    :param file: The file to read 
    '''
    try:
        with open(file, "r") as f:
            return f.readlines()
    except FileNotFoundError:    
        print(f"\n{Fore.RED + file} Not found! {Fore.RESET}")
        exit()

class Spider:

    def __init__(self, url, output, recursive, verbosity):
        
        self.url = url
        self.output = output
        self.recursive = recursive
        self.verbosity = verbosity
        
        #list used to store the external links of a given website
        self.target_links = []

        #list used to store the subdomains of a website, so it will be used in the recursive mode
        self.subdomains_list = []

        self.nbr_links = 0
        #links already scanned
        self.previous_links = []

        self.nbr_dirs = 0
        self.nbr_subdomains = 0

    def request_url(self, url):
        '''
        Function used to a request a link

        :param url: url to be requested
        '''
        try:
            return requests.get(url, timeout=3)
        except:
            return None

    def subfinder(self, *args):
        '''
        Discovering Websites Subdomains
        
        :param args: wordlist content
        '''
        
        for line in args:
            # http://example.com -> http://[subdomain].example.com
            test_url = self.url.split("://")[0] + "://" + line.strip("\n") + "." + self.url.split("://")[1]
            
            #request the new url
            response = self.request_url(test_url)
            
            if response:
                #if we got a response, this means we had find a subdomain
                self.nbr_subdomains += 1

                #if the mode is recursive, we add the subdomain to the subdomains list
                if self.recursive:
                    self.subdomains_list.append(test_url)
                
                #Print the result depending on the verbosity and the output file
                if self.output:
                    with open(self.output, "a") as file:
                        if self.verbosity >= 1:
                            file.write("[+] SubDomain --> " + test_url + "\n")
                        else:
                            file.write(test_url + "\n")
                else:
                    if self.verbosity >=1 : 
                        print(f"{Fore.GREEN}[+] SubDomain --> {Fore.RESET + test_url}")
                    else:
                        print(test_url)
            #if no response, means the subdomain is invalid
            else:
                if self.verbosity >= 2: 
                    if self.output:
                        with open(self.output, "a") as file:
                            file.write("[-] Invalid SubDomain --> " + test_url + "\n")
                    else:
                        print(f"{Fore.RED}[-] Invalid SubDomain --> {test_url + Fore.RESET}, ", end="\r")
            

    def dirfinder(self, *args):
        '''
        Discovering Hidden Dirs in Websites
        
        :param args: wordlist content
        '''
        for line in args:
            
            #http://example.com -> http://example.com/[dir]
            test_url = self.url  + line.strip("\n")
            #testing the new url
            response = self.request_url(test_url)
            if response:

                #if we got a response, means we had find a directory
                self.nbr_dirs += 1

                #Print the result depending on the verbosity and the output file                
                if self.output:
                    with open(self.output, "a") as file:
                        if self.verbosity >= 1:
                            file.write("[+] Dir --> " + test_url + "\n")
                        else:
                            file.write(test_url + "\n")
                else:
                    if self.verbosity >= 1:
                        print(f"{Fore.GREEN}[+] Dir --> {Fore.RESET + test_url}")
                    else:
                        print(test_url)

            #if no response, means the subdomain is invalid
            else:
                if self.verbosity >= 2:
                    if self.output:
                        with open(self.output, "a") as file:
                            file.write("[-] Invalid Dir --> " + test_url + "\n")
                    else:
                        print(f"{Fore.RED}[-] Invalid Dir --> {Fore.RESET + test_url}", end="\r")

        #if the mode is recursive, we will search for the dirs in subdomains
        if self.recursive and len(self.subdomains_list) > 0:

            for sub_url in self.subdomains_list:
            
                for line in args:
                    #http://www.example.com -> http://www.example.com/[dir]
                    test_url = sub_url + line.strip("\n")
                    response = self.request_url(test_url)
                    if response:
                        if self.output:
                            with open(self.output, "a") as file:
                                file.write("[+] SubDomain Dir --> " + test_url + "\n")

                        else:
                            print(f"{Fore.GREEN}[+] SubDomain Dir --> {Fore.RESET + test_url}")
                    

    def linkfinder(self, url, allinks):
        '''
        Extracting Links from websites
        
        :param url: url to scan
        :param allinks: bool indicates if we extract the external links
        '''
        try:

            response = requests.get(url)
            
            #using regex to extract links from html tags
            href_links = findall('(?:href=")(.*?)"', response.content.decode(errors= "ignore"))
            href_links.extend(findall('(?:href=\')(.*?)/\'', response.content.decode(errors= "ignore")))

            for link in href_links:
                
                #If there is a relative link, it will convert it to a full url
                link = parse.urljoin(url, link) 
                
                #The '#' refers to different things in same url, so we need to delete it to avoid url repeating 
                if "#" in link: 
                        link = link.split("#")[0]

                #if the link is not scanned previously
                if link not in self.previous_links:
                    
                    self.previous_links.append(link)
                    
                    if allinks:

                        self.nbr_links += 1

                        if self.output:
                            with open(self.output, "a") as file:
                                if self.verbosity >= 1:
                                    file.write("[+] Link --> " + link + "\n")
                                else:
                                    file.write(link + "\n")
                        else:
                            if self.verbosity >= 1:
                                print(f"{Fore.GREEN}[+] Link --> {Fore.RESET + link}")
                            else:
                                print(link)
                    
                        #To extract also the urls from the internal links
                        self.linkfinder(link, allinks) 

                    #To prevent printing external link like facebook, youtube ...
                    elif url in link and link not in self.target_links: 

                        self.target_links.append(link)
                        
                        self.nbr_links += 1

                        if self.output:

                            with open(self.output, "a") as file:
                                if self.verbosity >= 1:
                                    file.write("[+] Link --> " + link + "\n")
                                else:
                                    file.write(link + "\n")
                        else:
                            if self.verbosity >= 1:
                                print(f"{Fore.GREEN}[+] Link --> {Fore.RESET + link}")
                            else:
                                print(link)
                        
                        #To extract also the urls from the internal links
                        self.linkfinder(link, allinks) 
    
        except TypeError:
            pass

    def sub_linkfinder(self):

        if self.recursive and len(self.subdomains_list) > 0:
            
            for sub_url in self.subdomains_list:
                try:
                    response2 = requests.get(sub_url)
                    href_sub_links = findall('(?:href=")(.*?)"', response2.content.decode(errors= "ignore"))
                    href_sub_links.extend(findall('(?:href=\')(.*?)/\'', response2.content.decode(errors= "ignore")))
                
                    for sub_link in href_sub_links:
                        sub_link = parse.urljoin(sub_url, sub_link) #If there is a relative link, it will convert it to a full url
                        
                        if "#" in sub_link: #The # refers to different things in same url, so we need to delete it to avoid url repeating 
                            sub_link = sub_link.split("#")[0]
                            
                        if sub_url in sub_link and sub_link not in self.target_links: #To prevent printing external link like facebook, youtube ...
                            self.target_links.append(sub_link)
                            self.nbr_links += 1
                            if self.output:
                                with open(self.output, "a") as file:
                                    if self.verbosity >= 1:
                                        file.write("[+] SubDomain Link --> " + sub_link + "\n")
                                    else:
                                        file.write(sub_link + "\n")

                            else:
                                if self.verbosity >= 1:
                                    print(f"{Fore.GREEN}[+] SubDomain Link --> {Fore.RESET + sub_link}")
                                else:
                                    print(sub_link)

                            self.sub_linkfinder(sub_link) #To extract also the urls from the internal links

                except TypeError:
                    pass

parser = ArgumentParser(epilog=__doc__, usage=SUPPRESS, formatter_class=RawTextHelpFormatter)

parser.add_argument("url", nargs="?", default=None, metavar="URL", help="Target URL")

parser.add_argument("-o", "--output", dest="output", nargs="?", const="result.txt", help=f"Write the results into a file\nDefault: {getcwd()}/results.txt\n\n")
parser.add_argument("-v", "--verbose", dest="verbosity", action="count", default=0, help="-v: Shows the result alone\n-vv: Shows the description of each result\n-vvv: Shows also the non valid URL. Works just with -p and -s\n\n")
parser.add_argument("-q", "--quiet", action="store_true", default=False, help="Quiet Mode. Will not print the banner\n")

arg = parser.add_argument_group("arguments")

arg.add_argument("-a", "--all", dest="all", action="store_true", help="all actions combined\n\n")
arg.add_argument("--all-links", dest="allinks", action="store_true", help="Will print all the links on the website, even the external ones\n\n")
arg.add_argument("-d", "--dirs", dest="dirs", action="store_true", help="Discovering Websites' hidden directories. (Needs a wordlist)\n\n")
arg.add_argument("-l", "--links", dest="links", action="store_true", help="Extract Websites Links related to the url\n\n")
arg.add_argument("-r", "--recursive", action="store_true", help="exhausted crawl (recursively).\n\n")
arg.add_argument("-s", "--subdomains", dest="subdomains", action="store_true", help="Discovering Websites' Subdomains. (Needs a wordlist)\n\n")
arg.add_argument("-t", "--threads", dest="threads", type=int, default=10, help="Number of threads. (Default is 10)\n\n")
arg.add_argument("-w", "--wordlists", dest="wordlists", nargs="*", default=[], help="Wordlist files.\nIf combined with -sl, you should provide two wordlists\nThe first wordlist will be used with the first flag and so on\nIf -a is used, the first wordlist will be for dirs\n\n")

arguments = parser.parse_args()
if not arguments.quiet:
    print(banner)

if not arguments.url:
    parser.print_help()
    exit()

if not arguments.url.startswith("http://") and not arguments.url.startswith("https://"):
    print("Invalid URL Format, use http:// or https://")
    exit()

if not arguments.url.endswith("/"):
    arguments.url = arguments.url + '/'

if not arguments.all and not arguments.links and not arguments.dirs and not arguments.subdomains and not arguments.allinks:
    print("You should specify an action, use --help for more informations")
    exit()

if arguments.all:
    arguments.links = arguments.dirs = arguments.subdomains = True

nb_list_needed = 0
if arguments.subdomains:
    nb_list_needed += 1
if arguments.dirs:
    nb_list_needed += 1

if len(arguments.wordlists) < nb_list_needed:
    print("Invalid number of wordlists, use --help for more informations")
    exit()

filtered_wordlists = [None, None]

if arguments.subdomains and arguments.dirs:
    if "-ps" in argv or "-psl" in argv or "-pls" in argv:
        filtered_wordlists = arguments.wordlists
    else:
        filtered_wordlists = list(reversed(arguments.wordlists))

elif arguments.subdomains:
    filtered_wordlists[1] = arguments.wordlists[0]

elif arguments.dirs:
    filtered_wordlists[0] = arguments.wordlists[0]

crawler = Spider(arguments.url, arguments.output, arguments.recursive, arguments.verbosity)

threads = []

if arguments.links or arguments.allinks:
    
    threads.append(Thread(target=crawler.linkfinder, args=(arguments.url, arguments.allinks), daemon=True))

if arguments.subdomains:

    wordlist = read_file(filtered_wordlists[1])

    if len(wordlist) < arguments.threads or arguments.threads <=0:

        print(f"\n{Fore.RED}Error: {Fore.RESET}Number of threads should be lower than wordlist's size and higher than 0")
        exit()

    lists = prepare_list(wordlist, arguments.threads)
    
    for liste in lists:

        threads.append(Thread(target=crawler.subfinder, args=liste, daemon=True))

if arguments.dirs:

    wordlist = read_file(filtered_wordlists[0])
    
    if len(wordlist) < arguments.threads or arguments.threads <=0:

        print(f"\n{Fore.RED}Error: {Fore.RESET}Number of threads should be lower than wordlist's size and higher than 0")
        exit()

    nbr_sub_list = len(wordlist) // arguments.threads
    lists = prepare_list(wordlist, nbr_sub_list)
    
    for liste in list(lists):

        threads.append(Thread(target=crawler.dirfinder, args=(liste), daemon=True))


start = ctime()

print(f"\n{Fore.BLUE}[*] {Fore.RESET}Start at {start}\n")


for thread in threads:
    try:
        thread.start()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}[*]{Fore.RESET}Keyboard Interrupt is detected. Exiting ...")
        exit()

for thread in threads:
    try:
        thread.join()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}[*]{Fore.RESET}Keyboard Interrupt is detected. Exiting ...")
        exit()


print("\n\nResults:")
print("========")
if arguments.links or arguments.allinks:
    print(f"{crawler.nbr_links} links found")
if arguments.dirs:
    print(f"{crawler.nbr_dirs} dirs found ")
if arguments.subdomains:
    print(f"{crawler.nbr_subdomains} subdomains found ")

end = ctime()
print(f"\n\n{Fore.BLUE}[*] {Fore.RESET}Finish at {end}")
