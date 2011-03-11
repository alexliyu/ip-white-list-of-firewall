#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright Š 2010 alexliyu email:alexliyu2012@gmail.com
# This file is part of CDM SYSTEM.
#
# CDM SYSTEM is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 0.3 of the License, or (at your option) any later
# version. WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# CDM SYSTEM. If not, see <http://www.gnu.org/licenses/>.
#  Copyright Š 2010 alexliyu email:alexliyu2012@gmail.com
from cdm_plugin import *
from model import *
from google.appengine.api import urlfetch
from app import htmllib
from app.htmllib import HTMLStripper
from datetime import datetime, timedelta
from google.appengine.ext import webapp, db
from google.appengine.api.urlfetch_errors import DownloadError
from feedmodel import FeedList, FeedsList, AddmemFeed
import feedparser
from google.appengine.runtime import DeadlineExceededError
from time import sleep
from base import *
from app import url, gbtools

class Fetchdb(BaseRequestHandler):

		def __init__(self):
				BaseRequestHandler.__init__(self)
				self.current="config"


		def getdb(self,checknumber,page=None,*arg1,**arg2):
				#for i in FeedsList.all():
				#		i.fetch_stat=1
				#		i.put()
				checknumber=checknumber
				listit= FeedsList.all().filter('fetch_stat = ',1)
				feeds=listit.fetch(checknumber)
				i=0
				for feed in feeds:
						i+=1
						logging.info('start to fetch article,The No %s',i)
						try:
								self.__store_article(feed)
						except Exception,data:
								logging.error('the error is %s ',data)


    # Use a helper function to define the scope of the callback.

		def __store_article(self,feed):
				listits=FeedList()
				try:
					entry=Entry(key_name=feed.key())
					entry.title=feed.title
					entry.excerpt=feed.excerpt
					entry.author_name=feed.author_name
					entry.date=feed.date
					entry.content=self.__Parse_image(feed.content)
					entry.categorie_keys=feed.categorie_keys
					entry.entrytype=Category().get(feed.categorie_keys[0]).media
					entry.save(True)
					feed.fetch_stat=4
					feed.put()
				except Exception,data:
						logging.error('the db saved error is: %s',data)
						feed.fetch_stat=3
						feed.put()

				logging.info('adding the article,the name is %s',feed.title)

		def __Parse_image(self,content):
				images=htmllib.Parse_images_url(content)

				if images:
					try:
						for image in images:
								tmpimage=Media.all().filter('oldurl = ',image).get()
								if tmpimage!=None:
										content=gbtools.stringQ2B(content)
										content=htmllib.decoding(content).replace(image,tmpimage.PhotoUrl())

					except Exception,data:
						logging.info(data)
				return content
