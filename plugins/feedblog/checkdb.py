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
from google.appengine.ext import webapp
from feedmodel import FeedList,FeedsList, FeedSet
from google.appengine.ext import db
from base import *

##################################################################
#1.def getChecked():the main def
#2.def checkentry():check the categorie_keys,content of entry
#3.def checkfeedslist():check the feedslist,del the older than one month and change the value of fetch_stat is 3 to 0
#4.def
#
########################################################
class Checkdb(BaseRequestHandler):

		def __init__(self):
				BaseRequestHandler.__init__(self)
				self.current="config"

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

		def getChecked(self,checknumber,page=None,*arg1,**arg2):
				checknumber=checknumber
				try:
						feedset=FeedSet.all().fetch(1)
						feedset=feedset[0]
				except Exception:

						self.initDb()
						feedset=FeedSet.all().fetch(1)
						feedset=feedset[0]

				defDir=feedset.defDir
				defStat=feedset.defStat
				defDate=feedset.defDate
				fetchelimit=feedset.last_entry
				fetchllimit=feedset.last_feedslist+1


				# fix the stat
				self.changefeedstat(defDate,defStat,feedset,checknumber)
				# fix the entry
				result=self.checkentry(fetchelimit,defDir,defStat,defDate,feedset,checknumber)
				if result==True:
						logging.info('the Entry checked successful!!!')
						result=self.checkfeedslist(fetchllimit,defDir,defStat,defDate,feedset,checknumber)
						if result==True:
								logging.info('the FeedsList checked successful!!!')
								feedset.stat=True
						else:
								logging.info('the FeedsList checked fail!!!')
								feedset.stat=False
				else:
						logging.info('the Entry checked is fail,please check the db')
						feedset.stat=False


				feedset.last_checked = datetime.now()
				feedset.put()



		def changefeedstat(self,defDate,defStat,feedset,checknumber):
				i=0
				if defStat==True:
						feed_clean_date = datetime.now()-timedelta(days = 14)
						listit=FeedsList()
						#TODO the fetch_stat=2,is mean the feeds maybe can try to seconds fetch,so we change the stat=0
						feeds=listit.all().filter('date <',feed_clean_date).filter('fetch_stat = ',2).fetch(int(checknumber))
						logging.info('Start to change the feedslist stat')
						for feed in feeds:
								feed.fetch_stat=0
								i+=1
						db.put(feeds)
						logging.info('finish!fixed %s',i)
				else:
						logging.info('nothing need to be change')


				feedset.chnitemi = i
				feedset.put()





		def checkfeedslist(self,fetchllimit,defDir,defStat,defDate,feedset,checknumber):
				delitems = 0
				delitemi = 0
				listits=FeedsList()
				fetchllimit=self.__checklimit(fetchllimit,listits.all().count(),checknumber)
				feeds=listits.all().filter('fetch_stat < ',4).fetch(checknumber,fetchllimit)
				s=0
				i=0
				updated=[]
				logging.info('beging to check the feedslist for No %s to %s',fetchllimit,fetchllimit+checknumber)
				for feed in feeds:
						s+=1
						result=self.__checklistnull(feed,s)
						if result!=True:
								logging.info('delete the No. %s items',s)
								feed.delete()

								i+=1
				# check the datetime of lists,and del the older
						else:
								result=self.__checkliststat(feed,s,defDate,defStat)
								if result !=True:
									logging.info('delete the No. %s items',s)
									feed.delete()

									i+=1
								else:
										result=self.__checklisterr(feed,s,defDir)
										if result !=True:
												logging.info('delete the No. %s items',s)
												i+=1
												feed.delete()

				#finished the feedslist check
				#db.put(feeds)
				logging.info('The totel items is %s,and we fixed the %s',s,i)
				delitems=s
				delitemi=i

				feedset.delitems = delitems
				feedset.delitemi = delitemi
				feedset.last_feedslist=fetchllimit+s
				feedset.put()
				return True


		def checkentry(self,fetchelimit,defDir,defStat,defDate,feedset,checknumber):
				entryerrs=0
				entryerri=0
				listit=Entry()
				feeds=listit.all().filter('date > ',fetchelimit).filter('content = ',None).order('-date').fetch(checknumber)
				logging.info(len(feeds))
				s=0
				i=0
				l=datetime.strptime('1970-01-01',"%Y-%m-%d")
				updated = []
				logging.info('beging to check the entry for %s to NO.%s',fetchelimit,checknumber)
				for feed in feeds:
					s+=1
					l=feed.date
					result=self.__checknull(feed,s)
					if result!=True:
						logging.info('delete the No. %s items',s)
						feed.delete()
						i+=1
				#db.put(feeds)
				entryerrs=s
				entryerri=i
		# check the


				#feedset.put()
				feedset.entryerrs=entryerrs
				feedset.entryerri=entryerri
				feedset.last_entry=l
				feedset.put()
				return True

		def __checklistnull(self,feed,s):

				result=True
				logging.info('check the No. %s items',s)
				try:

					if len(feed.content)>0 and len(feed.excerpt)>0:
							return True
					else:
							if feed.fetch_stat > 2:
									logging.info('the content or excerpt is null!!')
									return False

							if (feed.fetch_stat == 0) and (len(feed.excerpt) == 0):
									logging.info('the excerpt is null')
									return False
							if (0 < feed.fetch_stat <= 2) and (len(feed.excerpt) == 0 or len(feed.content) == 0):
									logging.info('the items is null')
									return False
				except Exception,data:
					logging.info('the content or excerpt is null!!,so we delete it')
					return False


		def __checkliststat(self,feed,s,defDate,defStat):

				if defStat==True:
						logging.info('check older of the No. %s items',s)
						feed_clean_date = datetime.now()-timedelta(days = defDate)

						if feed.date < feed_clean_date:
								return False
						else:
								return True
				else:
						return True



		def __checklisterr(self,feed,s,defDir):
				logging.info('check item`s status of FeedsList')
				try:
						if len(feed.categorie_keys)> 0:
								return True
						else:
								logging.info('the category_key is lost,we try to fix it now')
								categorie_keys =self.__getcategorykey(feed.feed_link,defDir)
								if categorie_keys!=None:
										feed.categorie_keys=categorie_keys[0]
										feed.put()
										return True
								else:
										logging.info('we can not find the category_key,so del it')
										return False

				except Exception,data:
						logging.error('checked error is %s',data)
						return False


		def __checknull(self,feed,s):
				result=True
				logging.info('check the No. %s items',s)
				try:
					if len(feed.content)>0 and len(feed.categorie_keys)>0:
							result=True
					else:
							logging.info('the content or categorie_key is null!!')
							result=False
				except Exception,data:
					logging.info('the content or categorie_keys maybe null')
					result=False
				return result


		def __changstat(self,feedkey):
				listit=FeedsList.get(feedkey)
				listit.fetch_stat=0
				listit.put()



		def __getcategorykey(self,feed_url,defDir):

				resultkry=[]

				feedslug=FeedList.all().filter('feedurl = ',feed_url)
				if feedslug!=None:
						resultkey=self.__changdir(feedslug[0].acategory)

				else:
						logging.warning('the item of id is  %s, and change it to %s',feedslug.id,defDir)
						resultkey = self.__changdir(defDir)



				return resultkey


		def __changdir(self,slug):
						cats=[]
						newcatess=[]
						cats=Category.all().filter('slug = ',slug)
						newcatess=[cats[0].key()]
						categorie_keys=newcatess
						return categorie_keys
		def __checklimit(self,oldlimit,nowlimit,checknumber):
				tmp=oldlimit+checknumber
				if tmp >= nowlimit:
						tmp=0
				return tmp
