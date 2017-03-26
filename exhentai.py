import time
import telegram
from telegram import *
from telegram.ext import *
from telegram.ext.dispatcher import run_async
import os
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.DEBUG)
logger = logging.getLogger(__name__)
POSTS = {}

from client import Client
exhcli = Client()

import db as DB
def Btn(*args, **kwargs):
	if (len(args) == 2):
		return InlineKeyboardButton(args[0], callback_data=args[1], **kwargs)
	elif (len(args) == 1):
		return InlineKeyboardButton(args[0], callback_data="None", **kwargs)
	else:
		return None
def get_filters(search):
	params = {
		"f_doujinshi":1,
		"f_manga":1,
		"f_artistcg":1,
		"f_gamecg":1,
		"f_western":1,
		"f_non-h":0,
		"f_imageset":1,
		"f_cosplay":0,
		"f_asianporn":0,
		"f_misc":1,
		"f_apply":"Apply+Filter",
		"f_search":search
	}
	return params
def get_cmd_data(cmd, *args):
	cmd = cmd+";"
	for i in range(0, 3-1):
		try:
			cmd += str(args[i])
		except:
			pass
		cmd += ";"

	return cmd[:-1]

import math
class PostsList:
	def __init__(self, posts_ids):
		self.posts_list = None
		self.page_size = 5
		self.page_num = 1
		self.posts_count = 0
		self.add(posts_ids)
		
	def get_page(self):
		page_list = self.posts_list[self.page_num-1]
		return "\n\n".join(page_list)

	def switch_page(self, page_num):
		self.page_num = page_num
		return self.get_page()

	def add(self, posts_ids):
		i = 0
		if (self.posts_list):
			last_page = self.posts_list[len(self.posts_list) - 1]
			i = len(last_page)
		else:
			self.posts_list = [[]]
		for post_id in posts_ids:
			post = exhcli.get_post(post_id)
			if (i == self.page_size):
				i = 0
				self.posts_list.append([])
			self.posts_count += 1
			self.posts_list[len(self.posts_list)-1].append("/%d %s" % (self.posts_count, post.title))
			i += 1
			
		return self.posts_list

	def get_reply_markup(self):
		data = ";kek"
		pn = self.page_num
		lp = math.ceil((self.posts_count / 5))

		btns =[[
			Btn(    "|« " + "1"            ,       "1" + data),
			Btn(     "‹ " + str(pn-1)      , str(pn-1) + data),
			Btn(     "· " + str(pn) + " ·" , ".............."),
			Btn(str(pn+1) + " ›"           , str(pn+1) + data),
			Btn(  str(lp) + " »|"          ,   str(lp) + data)
			]]

		if (lp <= 5):
			for i in range(0, lp):
				page = str(i+1)
				if (int(page) == pn):
					page = "· " + page + " ·"
				btns[0][i] = Btn(page, page + data)
			for i in range(5, lp, -1):
				try:
					btns[0].pop(i-1)
				except:
					pass
		else:
			start = None
			if (pn < 4):
				start = 0
			if (pn > (lp - 2) - 1):
				start = (lp - 4) - 1
			if (start is not None):
				for i in range(start, start + 5):
					btn_num = i - start
					page = i+1
					page_str = str(page)
					if (page == pn):
						btns[0][btn_num] = Btn("· " + page_str + " ·", "closed")
					elif (page == 4 and pn < page):
						btns[0][btn_num] = Btn(page_str + " ›", page_str + data)
					elif (page == start + 2 and start != 0):
						btns[0][btn_num] = Btn("‹ " + page_str, page_str + data)
					elif (page == start + 1 and start != 0):
						btns[0][btn_num] = Btn("|« 1", "1" + data)
					elif (page == start + 5 and start == 0):
						btns[0][btn_num] = Btn(str(lp) + " »|", str(lp) + data)
					else:
						btns[0][btn_num] = Btn(page_str, page_str + data)
		try:
			if (len(btns[0]) == 1):
				btns.pop(0)
		except:
			pass
		btns.append([Btn("Add more results", "more;")])
		return InlineKeyboardMarkup(btns)

class PostsQueue:
	def __init__(self, posts_ids):
		self.posts_ids = posts_ids

	def show_post(self, message, post_index=0, post_image_index=0):
		post_id = self.posts_ids[post_index]
		post = exhcli.get_post(post_id, full=True)
		btns = [[Btn("Continue reading", get_cmd_data("continue", post_index, post_image_index+1))],
		[Btn("Next post", get_cmd_data("next", post_index+1, post_image_index)),Btn("View all %d images" % post.pages_count, get_cmd_data("all", post_index))]]
		post.send_image(exhcli, message, post_image_index, reply_markup=InlineKeyboardMarkup(btns))

	def show_all_posts(self, message, post_index):
		post_id = self.posts_ids[post_index]
		post = exhcli.get_post(post_id, full=True)
		btns = [[Btn("Next post", get_cmd_data("next", post_index+1, 0))]]
		all_images_cache = DB.get_all_images_cache()
		for i in range(1, post.pages_count):
			message = post.send_image(exhcli, message, i, all_images_cache)
		message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(btns))


@run_async
def start(bot, update, user_data):
	help_msg = "Hello. I'm currently in developing. I can only view all posts without any filters and download them as a zip archive.\n"
	help_msg += "/search - Search by words, tags, etc.\n"
	help_msg += "/all - View latest posts\n"
	help_msg += "/uncen - Uncensored galleries\n"
	help_msg += "/loli - Loli galleries\n"
	help_msg += "/yuri - Yuri galleries\n"
	help_msg += "/yaoi - Yaoi galleries\n"
	update.message.reply_text(help_msg)

@run_async
def allposts(bot, update, user_data):
	user_data["posts_list"] = PostsList(exhcli.get_posts_from_page("https://exhentai.org/"))
	update.message.reply_text(user_data["posts_list"].get_page(), reply_markup=user_data["posts_list"].get_reply_markup())

@run_async
def search(bot, update, user_data, args):
	params = {
		"f_doujinshi":1,
		"f_manga":1,
		"f_artistcg":1,
		"f_gamecg":1,
		"f_western":1,
		"f_non-h":1,
		"f_imageset":1,
		"f_cosplay":1,
		"f_asianporn":1,
		"f_misc":1,
		"f_apply":"Apply+Filter",
		"f_search":" ".join(args)
	}
	user_data["posts_ids"] = exhcli.get_posts_from_page("https://exhentai.org/", filters=params)
	user_data["page_num"] = 1
	update.message.reply_text(get_posts_list(user_data), reply_markup=get_switch_markup(user_data))

@run_async
def loli(bot, update, user_data):
	queue = PostsQueue(exhcli.get_posts_from_page("https://exhentai.org/", filters=get_filters("loli")))
	user_data["posts_queue"] = queue
	queue.show_post(update.message)

@run_async
def uncen(bot, update, user_data):
	queue = PostsQueue(exhcli.get_posts_from_page("https://exhentai.org/", filters=get_filters("uncensored")))
	user_data["posts_queue"] = queue
	queue.show_post(update.message)

@run_async
def yuri(bot, update, user_data):
	queue = PostsQueue(exhcli.get_posts_from_page("https://exhentai.org/", filters=get_filters("yuri")))
	user_data["posts_queue"] = queue
	queue.show_post(update.message)

@run_async
def yaoi(bot, update, user_data):
	queue = PostsQueue(exhcli.get_posts_from_page("https://exhentai.org/", filters=get_filters("yaoi")))
	user_data["posts_queue"] = queue
	queue.show_post(update.message)

@run_async
def filters(bot, update, user_data):
	update.message.reply_text("Soon...")

@run_async
def settings(bot, update, user_data):
	update.message.reply_text("Soon...")

@run_async
def imgurl(bot, update, args):
	url = " ".join(args)
	thumb_file = exhcli.download_img(url)
	update.message.reply_photo(thumb_file, caption=url)

@run_async
def gethtml(bot, update, args):
	url = " ".join(args)
	kek = open("kek.html", "w")
	kek.write(exhcli.get_html(url))
	kek.close()	


@run_async
def any_text(bot, update, user_data):
	text = update.message.text
	logging.info("ANY_TEXT")
	if (len(text) < 4):
		if (text[0] == "/"):
			try:
				num = int(text[1:])
				post_id = user_data["posts_ids"][num-1]
				post = POSTS[post_id]
				thumb = exhcli.download_img(post.thumb_url)
				thumb_name = thumb.name
				update.message.reply_photo(thumb, caption=(" ".join(gallery["tags"]))[:3000], reply_markup=InlineKeyboardMarkup([[Btn("Download zip", "zip;" + posts_id)]]), disable_web_page_preview=True)
				os.remove(thumb_name)
			except:
				pass

@run_async
def callback(bot, update, user_data):
	call = update.callback_query
	uid = call.from_user.id
	message = call.message
	chat_id = message.chat.id
	is_audio = message.audio is not None
	cmd, arg1, arg2 = call.data.split(";")

	if (cmd == "more"):
		posts_list = user_data["posts_list"]
		if (posts_list):
			site_page_num = posts_list.posts_count/5+1
			posts_list.add(exhcli.get_posts_from_page("https://exhentai.org/?page=%d" % site_page_num))
			message.edit_reply_markup(reply_markup=posts_list.get_reply_markup())
	elif (cmd == "zip"):
		gallery = POSTS[arg]["gallery"]
		msg = message.reply_text("Downloading...")
		zipf = exhcli.download_zip(msg, gallery)
		name = zipf.name
		message.reply_document(zipf)
		zipf.close()
		os.remove(name)
	elif (cmd == "continue" or cmd == "next"):
		queue = user_data["posts_queue"]
		message.edit_reply_markup(reply_markup=None)
		call.answer("Loading...")
		queue.show_post(message, int(arg1), int(arg2))
	elif (cmd == "all"):
		queue = user_data["posts_queue"]
		queue.show_all_posts(message, int(arg1))

	try:
		pn = int(cmd)
		posts_list = user_data["posts_list"]
		if (posts_list):
			message.edit_text(posts_list.switch_page(pn), reply_markup=posts_list.get_reply_markup())
	except:
		pass
	call.answer()


def main():
	# Create the EventHandler and pass it your bot's token.
	updater = Updater("261297388:AAHxTdGEyB1gkvgzurprsGfr32-o6fkm6FA")
	# Get the dispatcher to register handlers
	dp = updater.dispatcher	
	dp.add_handler(CommandHandler("start", start, pass_user_data=True))
	dp.add_handler(CommandHandler("all", allposts, pass_user_data=True))
	dp.add_handler(CommandHandler("img", imgurl, pass_args=True))
	dp.add_handler(CommandHandler("html", gethtml, pass_args=True))
	dp.add_handler(CommandHandler("search", search, pass_user_data=True, pass_args=True))
	dp.add_handler(CommandHandler("loli", loli, pass_user_data=True))
	dp.add_handler(CommandHandler("uncen", uncen, pass_user_data=True))
	dp.add_handler(CommandHandler("yuri", yuri, pass_user_data=True))
	dp.add_handler(CommandHandler("yaoi", yaoi, pass_user_data=True))
	dp.add_handler(CommandHandler("filters", filters, pass_user_data=True))
	dp.add_handler(CommandHandler("settings", settings, pass_user_data=True))
	dp.add_handler(MessageHandler(Filters.command, any_text, pass_user_data=True), group=1)
	dp.add_handler(CallbackQueryHandler(callback, pass_user_data=True))
	updater.start_polling()
	updater.idle()

if __name__ == '__main__':
	main()
