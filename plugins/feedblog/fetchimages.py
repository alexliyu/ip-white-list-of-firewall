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
from google.appengine.ext import webapp
from google.appengine.api.urlfetch_errors import DownloadError
from feedmodel import FeedList, FeedsList, AddmemFeed, Tempimages
import feedparser
from google.appengine.runtime import DeadlineExceededError
from time import sleep
from base import *
from app.htmllib import getImageInfo

class FetchImages(BaseRequestHandler):

		def __init__(self):
				BaseRequestHandler.__init__(self)
				self.current="fetchimages"


		def Getimages_blob(self,page=None,*arg1,**arg2):
				listit= Tempimages.all().filter('stat =',0)
				images=listit.fetch(10)
				i=0
				rpcs=[]
				for image in images:
						i+=1
						logging.info('start to fetch images,The No %s',i)
						try:


								rpc = urlfetch.create_rpc(10)
								name=htmllib.sid()+'.jpg'
								urlfetch.make_fetch_call(rpc, htmllib.encoding(image.oldurl))
								result = rpc.get_result()
								logging.info(result.status_code)
								if result.status_code == 200:
										result=self.__store_images(result.content,name,image)
								else:
										result=False
								if result:
										logging.info('Success!')
								else:
										logging.info('this one was Fail!')

						except Exception,data:
								logging.info(data)




		def Getimages(self,page=None,*arg1,**arg2):
				listit= Tempimages.all().filter('stat =',0)
				images=listit.fetch(10)
				i=0
				rpcs=[]
				for image in images:
						i+=1
						logging.info('start to fetch images,The No %s',i)
						try:


										rpc = urlfetch.create_rpc(10)
										name=htmllib.sid()+'.jpg'
										upload_url = blobstore.create_upload_url('/admin/tempupload')
										result = urlfetch.fetch(image.oldurl)
										boundary = '----------ThIs_Is_tHe_bouNdaRY_$'
										size, payload=htmllib.send_data('file',name, result.content,htmllib.encoding(image.oldurl,'utf-8'))
										urlfetch.make_fetch_call(rpc, url=upload_url,
														payload=payload,
														method=urlfetch.POST,
														headers={'Content-Type': 'multipart/form-data;boundary=%s '% boundary},
														allow_truncated=False)


						except Exception,data:
								logging.info(data)

					# Finish all RPCs, and let callbacks process the results.


		def __store_images(self,content,name,model):
				try:
						keyname=str(hash(model.oldurl))
						media=Media(key_name=keyname)
						media.mtype,media.width,media.height=getImageInfo(content)
						media.filename=name
						media.size=len(content)
						media.user=users.get_current_user()
						media.name=name
						media.blobfile=content
						media.oldurl=model.oldurl
						media.put()

						model.stat=1
						model.put()
						return True


				except Exception,data:
						model.stat=2
						logging.error('the db saved error is: %s',data)
