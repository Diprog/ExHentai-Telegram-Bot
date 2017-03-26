def get_html(self, url):
	global use_proxy
	r = None
	if (use_proxy):
		if (self.working_proxies):
			try:
				logging.info("Testing request")
				r = requests.get(url, cookies=self.cookies, proxies=self.working_proxies, timeout=10)
			except:
				logging.warn("Failed to get html by proxy %s (%d)" % (PROXIES[self.proxy_index], self.proxy_index))
				self.working_proxies = None
				self.proxies = self.get_not_used_proxy()
				r = None
		while r is None or len(r.text) < 300:
			try:
				logging.info("Testing request")
				r = requests.get(url, cookies=self.cookies, proxies=self.proxies, timeout=10)
				self.working_proxies = self.proxies
			except:
				logging.warn("Failed to get html by proxy %s (%d)" % (PROXIES[self.proxy_index], self.proxy_index))
				self.proxies = self.get_not_used_proxy()
	else:
		try:
			r = requests.get(url, cookies=self.cookies, timeout=5)
		except:
			use_proxy = True
			return self.get_html(url)
	return r.text

def get_not_used_proxy(self):
	global PROXIES
	if (self.proxy_index >= len(PROXIES)):
		PROXIES = get_proxies()
	proxy = PROXIES[self.proxy_index]
	proxies_param = {'https': "%s://%s" % (proxy["type"], proxy["addr"])}
	print(proxy)
	self.proxy_index += 1

	return proxies_param