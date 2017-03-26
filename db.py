import sqlite3
import json

def update_cookies(cookies):
	conn = sqlite3.connect("db.db")
	c = conn.cursor()
	c.execute("UPDATE SERVER SET data=? WHERE type='cookies'", (str(cookies).replace("'", "\""),))
	conn.commit()
	conn.close()

def get_cookies():
	conn = sqlite3.connect("db.db")
	c = conn.cursor()
	c.execute("SELECT * FROM SERVER WHERE type='cookies'")
	cookies = c.fetchone()[1].replace("'", "\"")
	print(cookies)
	conn.commit()
	conn.close()
	return json.loads(cookies)

def get_all_images_cache():
	conn = sqlite3.connect("db.db")
	c = conn.cursor()
	c.execute("SELECT * FROM IMAGES_CACHE")
	rows = c.fetchall()
	conn.close()
	cache = {}
	for row in rows:
		cache[row[0]] = row[1]
	return cache

def cache_image(file_id, url):
	conn = sqlite3.connect("db.db")
	c = conn.cursor()
	c.execute("INSERT INTO IMAGES_CACHE VALUES (?,?)", (url, file_id,))
	rows = c.fetchall()
	conn.commit()
	conn.close()

def get_image_cache(url):
	conn = sqlite3.connect("db.db")
	c = conn.cursor()
	c.execute("SELECT * FROM IMAGES_CACHE WHERE url=?", (url,))
	row = c.fetchone()
	if (row):
		return row[1]
	else:
		return None