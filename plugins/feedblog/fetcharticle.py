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
from app import htmllib,gbtools
from app.htmllib import HTMLStripper
from datetime import datetime, timedelta
from google.appengine.ext import webapp
from google.appengine.api.urlfetch_errors import DownloadError
from feedmodel import FeedList, FeedsList, AddmemFeed, Tempimages
import feedparser
from google.appengine.runtime import DeadlineExceededError
from time import sleep
from base import *

class Fetcharticle(BaseRequestHandler):

		def __init__(self):
				BaseRequestHandler.__init__(self)
				self.current="config"


		def getArticle(self,page=None,*arg1,**arg2):
				listit= FeedsList.all().filter('fetch_stat =',0)
				feeds=listit.fetch(5)
				i=0
				rpcs=[]
				for feed in feeds:
						i+=1
						logging.info('start to fetch article,The No %s',i)
						try:
								if feed.start_target!='nohtml':

										rpc = urlfetch.create_rpc(10)
										rpc.callback =self.__create_callback( rpc,feed)
										urlfetch.make_fetch_call(rpc, feed.link)
										rpcs.append(rpc)
								else:
									self.__store_article(feed.excerpt,feed)
						except Exception,data:
								logging.error('the rpc error is %s ',data)

					# Finish all RPCs, and let callbacks process the results.
				for rpc in rpcs:
						rpc.wait()


    # Use a helper function to define the scope of the callback.
		def __create_callback(self,rpc,feed):
				 return lambda: self.handle_result(rpc,feed)


		def handle_result(self, rpc,feed):
				logging.info('fetch new article %s,at %s'%(feed.link, datetime.now()))
				contenthtml=''
				try:
						result = rpc.get_result()
						if result.status_code == 200:
								if len(feed.start_target)!=0 and feed.start_target!='nohtml':
										contenthtml=htmllib.parsehtml(result.content,feed.feed_link,feed.link,feed.start_target,feed.allow_target,feed.mid_target,feed.end_target,feed.stop_target)
								else:
										contenthtml=feed.excerpt

								self.__store_article(contenthtml,feed)

								return True
						return False
				except Exception,data:
						logging.info('DownloadError in get %s.the error is %s',feed.link,data)
						return False

		def __store_article(self,contenthtml,feed):
				listits=FeedsList()
				entry=listits.get(feed.key())
				try:

						entry.content=htmllib.decoding(contenthtml)
						entry.fetch_stat=1
						images=htmllib.Parse_images_url(contenthtml)
						for image in images:
								key_name=str(hash(image))
								result=Tempimages.get_or_insert(key_name=str(hash(image)),oldurl=image)

								result.put()



				except Exception,data:
						entry.fetch_stat=2
						logging.info('the db saved error is: %s',data)
				entry.put()
				logging.info('adding the article,the name is %s',feed.title)
