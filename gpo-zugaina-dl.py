import urllib.request
import os
import sys
import re
from optparse import OptionParser
from bs4 import BeautifulSoup
from colors import color

def get(url):
	with urllib.request.urlopen(url) as response: 
		return response.read()

def sanitize(path):
	if path.endswith("/"):
		return path
	else:
		return path+"/"

def download_rec(prefix,overlay,package,path):
	
	url = "https://data.gpo.zugaina.org/"+overlay+"/"+package
	if path is not None:
		url = url + "/" + path
	else:
		path = "/"

	html = get(url)
	parsed_html = BeautifulSoup(html, "lxml")
	items = parsed_html.body.find_all('a')
	index = 5
	while index < len(items):
		href = items[index]['href']
		if options.verbose or options.pretend:
			decors="│   │   │   ├── "
			for _ in range(len(path.split("/"))-2):
				decors="│   " + decors
			print(decors[:-4]+"│")
			

		if href.find('/') != -1:
			#print(href + ' is dir ' + path)
			if options.verbose or options.pretend:
				print(decors+sanitize(href))
			if not options.pretend:
				os.makedirs(prefix+package+path+href, exist_ok=True)
			download_rec(prefix,overlay,package,path+href)
		else:
			if options.verbose or options.pretend:
				print(decors+href)
				
			if not options.pretend:
				txt = get(url+"/"+href) 
				file = open(prefix+package+path+href,"w")
				file.write(txt.decode("utf-8")) 
				file.close()
		index = index + 1
		
def search(text):
	html = get('https://gpo.zugaina.org/Search?search='+text)
	parsed_html = BeautifulSoup(html, "lxml")
	searchItems = parsed_html.body.find('div', attrs={'id':'search_results'}).find_all('a')

	if not searchItems:
		print(color("*", bold=True, fg_yellow=True) + ' No results are found for ' + color(text, bold=True))
		sys.exit(0)

	for searchItem in searchItems:
		strippedItem = searchItem.text.strip()
		print(color("*", bold=True, fg_green=True) + " " + color(strippedItem.split(' ', 1)[0], bold=True))
		print("\t" +color("Description: ",fg_green=True) + strippedItem.split(' ', 1)[1])

def download(prefix,overlay,package):
	if options.verbose or options.pretend:
		print(prefix)
		print("│")
		print("├── " +  sanitize(package.split("/")[0]))
		print("│   │")
		print("│   ├── " + sanitize(package.split("/")[1]))
	if not options.pretend:
		os.makedirs(prefix+package, exist_ok=True)
	download_rec(prefix,overlay,package,None);

def view_package_overlays(package):
	try:
		html = get('https://gpo.zugaina.org/' + package)
	except Exception:
		print(color("*", bold=True, fg_light_red=True) + ' Category or package ' + color(package, bold=True) + ' not exists')
		sys.exit(1)

	parsed_html = BeautifulSoup(html, "lxml")
	packages = parsed_html.body.find('div', attrs={'id':'ebuild_list'}).ul.find_all('div',recursive=False)
	category = package.split('/')[0]
	for package in packages:
		overlay = package['id']
		infos = package.li.find_all('div')
		name = infos[0].text
		keywords = infos[1].text
		license = "";

		directTexts = package.li.findAll(text=True, recursive=False)
		for directText in directTexts:
			if directText.find('License') != -1:
				license = directText.strip();

		print(color("*", bold=True, fg_green=True) + " " + color(category + "/" + name, bold=True))
		print("\t" +color("Keywords: ",fg_green=True) + keywords)
		print("\t" +color("License: ",fg_green=True) + license)
		print("\t" +color("Overlay: ",fg_green=True) + color(overlay, bold=True))

parser = OptionParser()
parser.add_option("-s", "--search", dest="search",
                  help="search a package", metavar="TEXT|CATEGORY/PACKAGE")
parser.add_option("-d", "--download", dest="download", nargs=3,
                  help="download package from overlay")
parser.add_option("-p", "--pretend", action="store_true", dest="pretend", 
				  default=False, help="display what will downloaded")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
				  default=False, help="run in verbose mode")
(options, args) = parser.parse_args()

if options.search:
	if options.search.find("/") == -1:
		search(options.search)
	else:
		view_package_overlays(options.search)
elif options.download:
	download(sanitize(options.download[0]),options.download[1],options.download[2])
