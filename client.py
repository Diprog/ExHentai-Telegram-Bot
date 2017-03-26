import requests
from bs4 import BeautifulSoup
import urllib.request
import os
from zipfile import ZipFile
import shutil
import db as DB

# POST JSON
"""
post = {
	"title":str,
	"url":str,
	"id":str,
	"thumb_url":str,

	"loaded":bool
	"tags":list,
	"images_urls":list
	"pages_count":int
}
"""
def load_headers(fname):
	headers = {}
	file = open(fname, "r")
	lines = file.read().split("\n")
	file.close()
	for line in lines:
		key,value = line.split(":")
		headers[key] = value
	return headers

class Post:
	def __init__(self, title=None, url=None, _id=None, thumb_url=None, loaded=False, tags=[], images_urls=[], pages_count=0):
		self.title = title
		self.url = url
		self.id = _id
		self.thumb_url = thumb_url
		self.loaded = loaded
		self.tags = tags
		self.images_urls = images_urls
		self.pages_count = pages_count

	def send_image(self, exhcli, message, image_index, all_images_cache=None, reply_markup=None):
		url = self.images_urls[image_index]
		file_id = None
		msg = None
		if (all_images_cache):
			file_id = all_images_cache.get(url)
		else:
			file_id = DB.get_image_cache(url)
		if (file_id):
			msg = message.reply_photo(photo=file_id, reply_markup=reply_markup)
		else:
			img = exhcli.download_img_from_post_url(url)
			msg = message.reply_photo(img, reply_markup=reply_markup)
			DB.cache_image(msg.photo[0].file_id, url)
			name = img.name
			img.close()
			os.remove(img.name)
		return msg

class Client:
	def __init__(self):
		self.cookies = DB.get_cookies()
		self.headers = load_headers("headers.txt")
		self.posts = {}
		#self.proxy_index = 0
		#self.proxies = self.get_not_used_proxy()
		#self.working_proxies = None
		
	def download_img(self, url):
		r = requests.get(url, stream=True, cookies=self.cookies)
		fname = url.split("/")
		fname = "imgs/" + fname[len(fname)-1]
		with open(fname, 'wb') as out_file:
			shutil.copyfileobj(r.raw, out_file)
		return open(fname, "rb")

	def download_img_from_post_url(self, url):
		html = self.get_html(url)
		soup = BeautifulSoup(html, 'html.parser')
		img_url = soup.find(id="img")["src"]
		img = self.download_img(img_url)
		return img

	def get_html(self, url, params={}):
		r = requests.get(url, headers=self.headers, cookies=self.cookies, params=params)
		try:
			self.cookies["lv"] = r.cookies["lv"]
			DB.update_cookies(self.cookies)
		except:
			pass
		return r.text
		

	def get_posts_from_page(self, url, filters={}):
		html = self.get_html(url, filters)
		posts = []
		soup = BeautifulSoup(html, 'html.parser')
		table = soup.find_all(attrs={"class":"itg"})
		rows = table[0].find_all("tr")
		post_id = None
		exists = False
		for i in range(1, len(rows)):
			row = rows[i]
			row_content = row.find_all("td")
			post = Post()
			for content in row_content:
				if (not post):
					break
				divs = content.find_all("div")
				for div in divs:
					a = div.find("a")
					img = div.find("img")
					
					if (a is not None):
						if ("/g/" in a["href"]):
							#id is a part of url for gallery
							#for example id is 1044376/3c3e553ca2
							#and gallery url is https://exhentai.org/g/1044376/3c3e553ca2/
							post.id = a["href"].split("/g")
							post.id = post.id[1][:-1]
							post_id = post.id
							#if a post was already loaded
							existing_post = self.posts.get(post.id)
							if (existing_post):
								post = None
								break
							post.title = a.contents[0]
							post.url = a["href"]
					#get thumbnail url
					if (img is not None):
						if ("/t/" in img["src"]):
							post.thumb_url = img["src"]
					try:
						#Sometimes "img" tag is missing and it's hidden as a "div" tag's contents
						#for example inits~exhentai.org~t/d7/af/d7af8f537fb2fc150a4e0724823b3ed1bba91c5d-1068052-1200-1701-jpg_l.jpg
						text = div.contents[0]
						if ("inits~exhentai.org" in text):
							post.thumb_url = "https://exhentai.org/" + text.split("~")[2]
					except:
						pass
			#not None
			if (post):
				self.posts[post_id] = post
			posts.append(post_id)
			print("###########")
			print(self.posts[post_id].__dict__)
		return posts

	def load_post(self, post, all_images=True):
		html = self.get_html(post.url)
		soup = BeautifulSoup(html, 'html.parser')
		
		full_tags = []
		images_urls = []
		pages_count = 0

		#Find tags
		tag_box = soup.find(id="taglist")
		rows = tag_box.find_all("tr")
		for row in rows:
			tags = row.find_all("td")
			main_tag = tags[0].contents[0].replace(":", "_")
			main_tag = "#" + main_tag
			tags.pop(0)
			for tag in tags:
				try:
					a = tag.find("a")
					#full_tags.append(main_tag + a.contents[0].replace(" ", "_"))
					full_tags.append("#" + a.contents[0].replace(" ", "_"))
				except:
					pass
		
		#Get images count
		infos_box = soup.find(id="gdd")
		infos = infos_box.find_all("td")
		for info in infos:
			try:
				text = info.contents[0]
				if ("pages" in text):
					pages_count = int(text.split(" ")[0])
			except:
				pass


		#Get all images urls
		page = 0
		while len(images_urls) < pages_count:
			html = self.get_html(post.url + ("?p=%d" % page))
			soup = BeautifulSoup(html, 'html.parser')
			new_images_urls = []
			small_images = soup.find_all(attrs={"class":"gdtm"})
			for small_image in small_images:
				a = small_image.find("a")
				new_images_urls.append(a["href"])
			images_urls += new_images_urls
			page += 1

		#Save
		post.tags = full_tags
		post.images_urls = images_urls
		post.pages_count = pages_count
		post.loaded = True

	def get_post(self, post_id, full=False):
		post = self.posts[post_id]
		if (post):
			print("###########################")
			print(post.__dict__)
			print("###########################")
			if (full):
				if (post.loaded):
					return post
				else:
					self.load_post(post)
					return post
			else:
				return post
		else:
			return None


	def download_zip(self, message, post, func=None, **kwargs):
		fname = post.id.replace("/", ".") + ".zip"
		myzip = ZipFile(fname, 'w')
		downloaded = 0
		for url in post.images_urls:
			html = self.get_html(url)
			soup = BeautifulSoup(html, 'html.parser')
			img_url = soup.find(id="img")["src"]
			img = exhcli.download_img(img_url)
			name = img.name
			myzip.write(name)
			img.close()
			os.remove(name)
			downloaded += 1
			message.edit_text("Downloading... (%d/%d)" % (downloaded, post.pages_count))
		myzip.close()
		return open(fname, "rb")