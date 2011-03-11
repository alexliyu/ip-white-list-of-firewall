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
from app.htmllib import HTMLStripper
from datetime import datetime, timedelta
from google.appengine.ext import webapp
from google.appengine.api.urlfetch_errors import DownloadError
from google.appengine.runtime import DeadlineExceededError
from google.appengine.ext import db
from pushmodel import PushList,PushMethod
from pusharticle import Pusharticle
from time import sleep
from base import *
import app.htmllib



class PushHandler(BaseRequestHandler):
	def __init__(self):
		BaseRequestHandler.__init__(self)
		self.current="pushblog"

	def get(self):
		if self.param('delid')=='':
			listit = PushList()
			querys = listit.all()
			feedDetal=''
			self.template_vals.update({'list':querys,'categories':Category.all(),'website':list(PushMethod().Get_name())})
			content=template.render('plugins/pushblog/pushblog.html',self.template_vals)
			self.render2('views/admin/setup_base.html',{'m_id':'pushblog_setup','content':content})
		else:
			listit = PushList()
			logging.info(self.param('delid'))
			querys=listit.get(self.param('delid'))
			querys.delete()
			self.redirect('/admin/pushblog/setup')



	def post(self):
		query = PushList()
		query.name =self.param('name')
		query.pushurl= self.param('website')
		query.username = self.param('username')
		query.password = self.param('password')
		query.acategory=self.param('acategory')
		query.category=self.param('category')
		query.put()

		self.get()



class pushblog(Plugin):
	def __init__(self):
		Plugin.__init__(self,__file__)
		self.author="李昱"
		self.authoruri="http://alexliyu.blog.163.com"
		self.uri="http://alexliyu.blog.163.com"
		self.description="feedblog Plugin for you to add enty."
		self.name="Pushblog"
		self.version="0.01"
		self.register_urlhandler('/admin/pushblog',pushblog)
		self.register_urlhandler('/admin/pushblog/setup',PushHandler)
		self.register_urlhandler('/robot/pusharticle',Pusharticle)
		self.register_setupmenu('pushblog_setup',_('Push'),'/admin/pushblog/setup')


	def get(self,page):
		return '''<h3>Pushblog Plugin</h3>
			   <p>This is a system plugin for cdm.
			   <br>Also a plugin for Push the article or rss to the other website</p>
			   <h4>feature</h4>
			   <p><ol>
			   <li>Add the time and date for rss</li>
			   <li>Add the speed for Push</li>
			   <li>Feedblog <a href="/admin/pushblog/setup">Setup</a></li>
			   </ol></p>
				'''


	def post(self,page):
		query = PushList()
		query.name =self.param('name')
		query.pushurl= self.param('website')
		query.username = self.param('username')
		query.password = self.param('password')
		query.acategory=self.param('acategory')
		query.category=self.param('category')
		query.put()
		return self.get(page)


class Pusharticle(Pusharticle):
		def get(self):
				self.Push()
