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
from base import *
from google.appengine.ext import db
from datetime import datetime, timedelta
from google.appengine.api import memcache

class FeedsList(db.Model):
		author_name = db.StringProperty()
		title = db.StringProperty(multiline=False,default='')
		date = db.DateTimeProperty(auto_now_add=True)
		tags = db.StringListProperty()
		categorie_keys=db.ListProperty(db.Key)
		link= db.StringProperty(multiline=False,default='')
		excerpt=db.TextProperty()
		feed_link= db.StringProperty(multiline=False,default='')
		abconf = db.StringProperty(multiline=False,default='0')
		start_target = db.StringProperty(multiline=False,default='nohtml')
		mid_target = db.StringProperty(multiline=False,default='nohtml')
		end_target = db.StringProperty(multiline=False,default='nohtml')
		allow_target = db.StringProperty(multiline=False,default='nohtml')
		stop_target= db.StringProperty(multiline=False,default='nohtml')
		fetch_stat=db.IntegerProperty(default=0)
		content=db.TextProperty()

class FeedList(db.Model):
		name = db.StringProperty(multiline=False,default='alexliyu')
		feedurl =db.StringProperty(multiline=False,default='http://alexliyu.blog.163.com/rss')
		latest =db.StringProperty(multiline=False,default='first')
		last_retrieved =db.DateTimeProperty(default = datetime.today().fromtimestamp(0))
		acategory =db.StringProperty(default='douban')
		abconf = db.StringProperty(multiline=False,default='0')
		start_target = db.StringProperty(multiline=False,default='nohtml')
		allow_target = db.StringProperty(multiline=False,default='nohtml')
		mid_target = db.StringProperty(multiline=False,default='nohtml')
		end_target = db.StringProperty(multiline=False,default='nohtml')
		stop_target= db.StringProperty(multiline=False,default='nohtml')

class FeedSet(db.Model):
		defDate = db.IntegerProperty(default=3600)
		defStat =db.BooleanProperty(default=True)
		defDir=db.StringProperty(default='')
		last_checked = db.DateTimeProperty(default = datetime.today().fromtimestamp(0))
		stat = db.BooleanProperty(default=False)
		delitems = db.IntegerProperty(default=0)
		delitemi = db.IntegerProperty(default=0)
		chnitemi = db.IntegerProperty(default=0)
		entryerrs=db.IntegerProperty(default=0)
		entryerri=db.IntegerProperty(default=0)
		last_entry=db.DateTimeProperty()
		last_feedslist=db.IntegerProperty(default=0)
		check_db_num=db.IntegerProperty(default=50)
		fetch_db_num=db.IntegerProperty(default=50)
		imgchecked_num=db.IntegerProperty(default=0)
		last_imgchecked=db.DateTimeProperty()

class Tempimages(db.Model):
		oldurl=db.StringProperty()
		newurl=db.StringProperty()
		stat=db.IntegerProperty(default=0)
		greatdate=db.DateTimeProperty(auto_now_add=True)
		parsedate=db.DateTimeProperty()



class AddmemFeed(BaseRequestHandler):
		def __init__(self):
				BaseRequestHandler.__init__(self)
				self.current="config"


		def get_mem(self):
				result=self.get_memFeed()
				if result==None :
						result=self.render_memFeed()

				return result


		def get_memFeed(self):
				memFeed = memcache.get("memFeed")
				if memFeed is not None:
						return memFeed
				else:
						return None

		def render_memFeed(self):
				try:
						listit = FeedsList()
						feeds = listit.all().filter('fetch_stat =',0).fetch(100)
						logging.info('loading the temp feeds from db')
						return list(feeds)
				except Exception,data:
						logging.error('the memcache error is %s',data)
						return None

		def replace_memFeed(self,memFeed):
				try:
						if not memcache.replace("memFeed", memFeed, time=3600):
								memcache.add("memFeed", memFeed, 3600)
						logging.info('replace the memcache now!')
						return True
				except Exception,data:
						logging.error('the memcache is not this key, and error is  %s',data)
						return False

		def edit_memFeed(self,key,content,stat):
				try:
						memFeed=self.get_memFeed()
						memFeed.get(key).content=content
						memFeed.get(key).fetch_stat=stat
						self.replace_memFeed(memFeed)
				except Exception,data:
						logging.error('the error is %s',data)
						return False





		def flush_db(self,memFeed):
				try:
						listit = self.render_memFeed()
						for flush_key in memFeed:
								if flush_key.fetch_stat!=0:
										listit.get(flush_key.key()).fetch_stat=flush_key.fetch_stat

						listit.put()
						return True
						logging.info('flush the memcache into the db')

				except Exception,data:
						logging.error('the db error is %s',data)
						return False

		def check_memFeed(self):
				memFeed=self.get_memFeed()
				if memFeed!=None:
						try:
								stat=self.flush_db(memFeed)
								if stat==True:
										memFeed=self.render_memFeed()
										dbstat=self.replace_memFeed(memFeed)
										if dbstat==True:
												logging.info('the memcache is flash now')
										else:
												logging.warning('sorry, i can not flush the memcache!')
								else:
										logging.warning('the memcache replace fail!')
						except Exception,data:
								logging.error('the error is %s',data)


				else:
						logging.warning('oh,my gods,the memcache is lost!!!!please run the check of feedblog')
						try:
								memFeed = self.render_memFeed()
								stat=memcache.add('memFeed', memFeed, 3600)

						except Exception,data:
								logging.error('add new db to the memcache had a error %s',data)
