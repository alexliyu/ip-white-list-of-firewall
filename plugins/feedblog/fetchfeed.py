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
from app.htmllib import HTMLStripper
from google.appengine.ext import webapp
from google.appengine.api.urlfetch_errors import DownloadError
from google.appengine.runtime import DeadlineExceededError
from feedmodel import FeedList,FeedsList
from base import *
import feedparser
from app import htmllib


class Fetchfeed(BaseRequestHandler):

		def __init__(self):
				BaseRequestHandler.__init__(self)
				self.current="fetchfeed"


		def getFeed(self,page=None,*arg1,**arg2):
				listit = FeedList()
				feeds = listit.all()
				#db.delete(feeds)
				#feed=FeedsList().all()
				#db.delete(feed)
				#entry=Entry().all()
				#db.delete(entry)
				feedscount=feeds.count()
				Strmessages=''
				Feedstat=''
				logging.info('start to fech feed')
				feed_retrieval_deadline = datetime.now()-timedelta(minutes = 1200)
				for feed in feeds:

					if feed.last_retrieved > feed_retrieval_deadline:
					#    #if feed.feedurl!='http://alexliyu.blog.163.com/rss/ ':
							logging.info('Skipping feed %s.',feed.feedurl)
							continue

					logging.info('Getting feed %s.',feed.feedurl)
					try:

							result = urlfetch.fetch(feed.feedurl)
					except Exception:
							logging.warning('Could not get feed %s ,and the fetch is restart now' % feed.feedurl)
							feed.last_retrieved =datetime.now()
							feed.put()
							break
					if result.status_code == 200:
							self.__parse_feed(page,result.content,feed.feedurl, feed.stop_target,feed.acategory,feed.latest,feed.start_target,feed.mid_target,feed.end_target,feed.allow_target)

							feed.last_retrieved =datetime.now()
							feed.put()

					elif result.status_code == 500:
							logging.error('Feed %s returned with status code 500.' %feed.feedurl)
					elif result.status_code == 404:
							logging.error('Error 404: Nothing found at %s.' % feed.feedurl)




		def __parse_feed(self,page,feed_content, feed_url, stop_target, acategory,feed_latest,start_target,mid_target,end_target,allow_target):
				feed = feedparser.parse(feed_content)
				i=0
				dead_i=0
				for entry in feed.entries:
						logging.info('start parse feed,the dead_i is %s',dead_i)
						title = htmllib.decoding(entry.title)
						hashkey=str(hash(title))
						categorie_keys=[]
						content=''
						date_published=datetime.now()
						author_name=''
						Mystat=True
						if self.__feedslist_check(hashkey)==False:
							try:
									i+=1
									url=''
									logging.info('beging to add new article No. %s',i)
									if(entry.has_key('feedburner_origlink')):
											url = entry.feedburner_origlink
									else:
											url = entry.link
									if entry.has_key('content'):
											content = entry.content[0].value
									else:
											content = entry.description
									if entry.has_key('author'):
											author_name=entry.author
									else:
											author_name="转载"
									stripper = HTMLStripper()
									stripper.feed(title)
									title =stripper.get_data()
									content = htmllib.decoding(content)
									content = htmllib.GetFeedclean(url,content,stop_target)
									if(entry.has_key('updated_parsed')):
											date_published = datetime(*entry.updated_parsed[:6])
									else:
											date_published =datetime.now()
									cats=[]
									newcatess=[]
									cats=Category.all().filter('slug = ',acategory)
									newcatess=[cats[0].key()]
									categorie_keys=newcatess
							except Exception,data:
									logging.warn('this like something happened,the error is %s',data)

							try:
									feedresult=self.__store_article(hashkey,title, url, categorie_keys, content,date_published, author_name,acategory,feed_url,start_target,mid_target,end_target,stop_target,allow_target)
									if feedresult==True:
											logging.info('The No.%s  is fetched to the db',i)
									else:
											logging.error('The No.%s is fetched Fail',i)
											Mystat=False
							except Exception,data:
									logging.warning('the error is %s',data)
									Mystat=False

						else:
							logging.info('skip this article,it is aready have')





		def __store_article(self,hashkey,title, url, categorie_keys, content,date_published, author_name,acategory,feed_link,start_target,mid_target,end_target,stop_target,allow_target):
				try:
						entry=FeedsList.get_by_key_name(hashkey)
						if not entry:
								entry=FeedsList(key_name=hashkey)
								entry.title=htmllib.decoding(title)
								entry.link=url
								entry.start_target=start_target
								entry.mid_target=mid_target
								entry.end_target=end_target
								entry.allow_target=allow_target
								entry.stop_target=stop_target
								entry.excerpt=content
								entry.author_name=htmllib.decoding(author_name)
								entry.categorie_keys= categorie_keys
								entry.feed_link=feed_link
								try:
										entry.date=datetime.strptime(date_published[:-6],'%a, %d %b %Y %H:%M:%S')
								except:
										try:
												entry.date=datetime.strptime(date_published[0:19],'%Y-%m-%d %H:%M:%S')
										except:
												entry.date=datetime.now()

								entry.put()
								return True
				except Exception,data:
						logging.error('the db saved error is: %s',data)
						return False


		def __feedslist_check(self,hashkey):
				listits=FeedsList()
				entry=listits.get_by_key_name(hashkey)
				if entry:
						return True
				else:
						return False
