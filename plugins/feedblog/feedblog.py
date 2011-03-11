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


from cdm_plugin import *
from model import *
from google.appengine.api import urlfetch
from app import htmllib
from app.htmllib import HTMLStripper
from datetime import datetime, timedelta
from google.appengine.ext import webapp
from google.appengine.api.urlfetch_errors import DownloadError
from google.appengine.runtime import DeadlineExceededError
from google.appengine.ext import db
from feedmodel import FeedList, FeedsList, AddmemFeed, FeedSet
from fetchdb import Fetchdb
from time import sleep
from base import *
from fetchfeed import Fetchfeed
from checkdb import Checkdb
from fetcharticle import Fetcharticle
from fetchimages import FetchImages
from checkdb import Checkdb
from checkimage import Checkimage
import feedparser
from test import Testme



class FeedHandler(BaseRequestHandler):
	def __init__(self):
		BaseRequestHandler.__init__(self)
		self.current="config"

	def get(self):
		if self.param('delid')=='':
			listit = FeedList()
			querys = listit.all()
			feedDetal=''
		else:
			listit = FeedList()
			querys=listit.all().filter('name =',self.param('delid')).fetch(1)
			for query in querys:
			    query.delete()
			self.redirect('/admin/feedblog/setup')
			self.response.set_status(301)
		self.template_vals.update({'list':querys})
		self.template_vals.update({'categories':Category.all()})
		content=template.render('plugins/feedblog/feedblog.html',self.template_vals)
		self.render2('views/admin/setup_base.html',{'m_id':'feedblog_setup','content':content})

	def post(self):
		query = FeedList()
		query.name =self.param('name')
		query.feedurl= self.param('feedurl')
		query.abconf = self.param('abconf')
		query.acategory=self.param('acategory')
		query.allow_target=self.param('allow_target')
		query.start_target=self.param('start_target')
		query.mid_target=self.param('mid_target')
		query.end_target=self.param('end_target')
		query.stop_target=self.param('stop_target')
		query.put()

		self.get()



class feedblog(Plugin):
	def __init__(self):
		Plugin.__init__(self,__file__)
		self.author="李昱"
		self.authoruri="http://alexliyu.blog.163.com"
		self.uri="http://alexliyu.blog.163.com"
		self.description="feedblog Plugin for you to add enty."
		self.name="feedblog"
		self.version="0.3"
		self.register_urlhandler('/robot/fetchfeed',Fetchfeeds)
		self.register_urlhandler('/robot/checkmem',AddmemFeed)
		self.register_urlhandler('/robot/fetcharticle',Fetcharticle)
		self.register_urlhandler('/robot/fetchdb',Fetchdb)
		self.register_urlhandler('/robot/checkdb',Checkdb)
		self.register_urlhandler('/admin/feedblog/setup',FeedHandler)
		self.register_urlhandler('/admin/feedblog/test',Testme)
		self.register_urlhandler('/robot/fetchimages',FetchImages)
		self.register_urlhandler('/robot/checkimage',Checkimage)
		self.register_setupmenu('feedblog_setup',_('collect'),'/admin/feedblog/setup')

		try:
				result=FeedSet().all().fetch(1)[0]
		except Exception,data:
				logging.info(data)
				self.initDb()

	def initDb(self):
				feedset=FeedSet()
				feedset.delitems = 0
				feedset.delitemi = 0
				feedset.chnitemi = 0
				feedset.entryerrs=0
				feedset.entryerri=0
				feedset.defDir='my'
				feedset.defStat=True
				feedset.defDate=60
				feedset.stat=False
				feedset.put()

	def get(self,page):
		return '''<h3>Feedblog Plugin</h3>
			   <p>This is a system plugin for cdm. <br>Also a plugin for fetch the article or rss into the cdm</p>
			   <h4>feature</h4>
			   <p><ol>
			   <li>Add the time and date for rss</li>
			   <li>Add the speed for fetch</li>
			   <li>Feedblog <a href="/admin/feedblog/setup">Setup</a></li>
			   </ol></p>
				'''


	def post(self,page):
		query = FeedList()
		query.name =page.param('name')
		query.feedurl= page.param('feedurl')
		query.abconf = page.param('abconf')
		query.acategory=page.param('acategory')
		query.start_target=self.param('start_target')
		query.allow_target=self.param('allow_target')
		query.mid_target=self.param('mid_target')
		query.end_target=self.param('end_target')
		query.stop_target=self.param('stop_target')
		query.put()
		return self.get(page)




class Fetchfeeds(Fetchfeed):
		def get(self):
				listit = FeedList()
				feeds = listit.all()
				listits=FeedsList()
				self.getFeed()

class FetchImages(FetchImages):
		def get(self):
				if Blog().all().fetch(1)[0].blobstore:
						self.Getimages()
				else:
						self.Getimages_blob()

class AddmemFeed(AddmemFeed):
		def get(self):
				self.check_memFeed()


class Fetcharticle(Fetcharticle):
		def get(self):
				self.getArticle()

class Fetchdb(Fetchdb):
		def get(self):
				self.getdb(FeedSet.all().fetch(1)[0].fetch_db_num)


class Checkimage(Checkimage):
		def get(self):
				self.check(50)


class Checkdb(Checkdb):
		def get(self):
				self.getChecked(FeedSet.all().fetch(1)[0].check_db_num)

class Testme(Testme):
		def get(self):
				content=template.render('plugins/feedblog/test.html',{'id':'feedblog_test'})
				self.render2('views/admin/setup_base.html',{'m_id':'feedblog_test','content':content})

		def post(self):
				url= self.param('url')
				start_target=self.param('start_target')
				if not start_target:
						start_target='nohtml'
				allow_target=self.param('allow_target')
				if not allow_target:
						allow_target='nohtml'
				mid_target=self.param('mid_target')
				if not mid_target:
						mid_target='nohtml'
				end_target=self.param('end_target')
				if not end_target:
						end_target='nohtml'
				stop_target=self.param('stop_target')
				if stop_target:
						stop_target=htmllib.decoding(stop_target)
				else:
						stop_target='nohtml'
				result=self.dotest(url,start_target,mid_target,end_target,allow_target,stop_target)
				if result==False:
					self.write ('there is something wrong,please try again')
