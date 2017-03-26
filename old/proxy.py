def get_proxies():
	r = req.get("http://www.socks-proxy.net/")
	html = r.text
	soup = BeautifulSoup(html, 'html.parser')
	table = soup.find(id="proxylisttable")
	rows = table.find("tbody").find_all("tr")
	proxies = {"DE":[], "others":[]}
	for row in rows:
		content = row.find_all("td")
		try:
			ip = content[0].contents[0]
			port = content[1].contents[0]
			code = content[2].contents[0]
			country = content[3].contents[0]
			version = content[4].contents[0]
			proxy = {"addr":ip+":"+port, "type":version.lower(), "code":code}
			if (code == "DE"):
				proxies["DE"].append(proxy)
			else:
				proxies["others"].append(proxy)
		except:
			pass

	return proxies["DE"] + proxies["others"]

def get_https_proxies():
	r = req.get("http://www.us-proxy.org/")
	html = r.text
	soup = BeautifulSoup(html, 'html.parser')
	table = soup.find(id="proxylisttable")
	rows = table.find("tbody").find_all("tr")
	proxies = {"DE":[], "others":[]}
	for row in rows:
		content = row.find_all("td")
		try:
			ip = content[0].contents[0]
			port = content[1].contents[0]
			code = content[2].contents[0]
			country = content[3].contents[0]
			anonymity = content[4].contents[0]
			google = content[5].contents[0]
			version = "https" if (content[6].contents[0] == "yes") else "http"
			if (version == "https"):
				proxy = {"addr":ip+":"+port, "type":version.lower(), "code":code}
				if (code == "DE"):
					proxies["DE"].append(proxy)
				else:
					proxies["others"].append(proxy)
		except:
			pass

	return proxies["DE"] + proxies["others"]

PROXIES = get_https_proxies()
PROXIES += get_proxies()