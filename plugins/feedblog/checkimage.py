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
from feedmodel import FeedSet

class Checkimage(BaseRequestHandler):

		def __init__(self):
				BaseRequestHandler.__init__(self)
				self.current="checkimage"


		def check(self,checknumber,page=None,*arg1,**arg2):
				#for i in FeedsList.all():
				#		i.fetch_stat=1
				#		i.put()
				checknumber=checknumber
				listit= Entry().all()
				model=FeedSet().all().fetch(1)[0]
				latest=model.last_imgchecked
				last_imgchecked=datetime.strptime('1970-01-01',"%Y-%m-%d")
				if not latest:
						last_imgchecked=datetime.strptime('1970-01-01',"%Y-%m-%d")
				if model.imgchecked_num==None or model.imgchecked_num>Blog().all().fetch(1)[0].entrycount:
						model.imgchecked_num=0
						model.put()
				i=model.imgchecked_num
				entries=listit.filter('date > ',latest).order('-date').fetch(checknumber)
				for entry in entries:
						i+=1
						logging.info('start to check article,The No %s',i)
						content=''
						last_imgchecked=datetime.strptime('1970-01-01',"%Y-%m-%d")
						try:
								content=self.__Parse_image(entry)
								if content:
										logging.info('we found the image,the title is %s',entry.title)
										entry.content=content
										entry.put()
								last_imgchecked=entry.date

						except Exception,data:
								logging.error('the error is %s ',data)
								pass

				model.imgchecked_num=i
				model.last_imgchecked=last_imgchecked
				model.put()




		def __Parse_image(self,entry):

				images=htmllib.Parse_images_url(entry.content)
				content=''

				if images:
					try:
						for image in images:
								tmpimage=Media.all().filter('oldurl = ',image).get()
								if tmpimage!=None:
										content=gbtools.stringQ2B(content)
										content=htmllib.decoding(entry.content).replace(image,tmpimage.PhotoUrl())
								else:
										pass

					except Exception,data:
						return None
					return content
				else:
						return None
