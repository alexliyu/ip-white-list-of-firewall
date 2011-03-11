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
from app import htmllib
from google.appengine.api import urlfetch
import urllib
import Cookie
from app.htmllib import HTMLStripper
from google.appengine.api.urlfetch_errors import DownloadError
from google.appengine.runtime import DeadlineExceededError
from app.gbtools import stringQ2B
from google.appengine.api import mail
from xml.sax.saxutils import unescape

class PushsList(db.Model):
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
		fetch_stat=db.IntegerProperty(default=0)
		content=db.TextProperty()

class PushList(db.Model):
		name = db.StringProperty(multiline=False,default='alexliyu')
		pushurl =db.StringProperty(multiline=False,default='http://blog.163.com/common/targetgo.s')
		username=db.StringProperty(multiline=False,default='alexliyu')
		password=db.StringProperty(multiline=False,default='password')
		latest =db.DateTimeProperty()
		last_retrieved =db.DateTimeProperty(default = datetime.today().fromtimestamp(0))
		acategory =db.StringProperty()
		category=db.StringProperty()
		pushnum=db.IntegerProperty(default=0)
		pushtime=db.IntegerProperty(default=0)

class PushSet(db.Model):
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
		last_entry=db.IntegerProperty(default=0)
		last_feedslist=db.IntegerProperty(default=0)
		check_db_num=db.IntegerProperty(default=50)
		fetch_db_num=db.IntegerProperty(default=50)
		imgchecked_num=db.IntegerProperty(default=0)

class PushMethod():
		def Get_name(self,key=None):
				method=dict((['blog.163.com','Get_blog163'],
						['qzone.qq.com','Get_qzone'],
						['t.sina.com.cn','Get_sina_msgs'],
						['t.qq.com','Get_qq_msgs']
				))
				if key:
						return method[str(key)]
				else:
						return method

		def Get_Method(self,key,**kwargs):
				method=self.Get_name(key)
				result=self.Do_Method(method,**kwargs)
				return result

		def Do_Method(self,method,**kwargs):
				result=getattr(self,method)(**kwargs)
				#if method=='blog163':
				#		result=self.Get_blog163(**kwargs)
				#elif method=='qzone':
				#		result=self.Get_qzone(**kwargs)
				#elif method=='sinamsg':
				#		result=self.Get_sina_msgs(**kwargs)
				return result

		def Get_blog163(self,model,pushitem,**kwargs):
			try:
				form_fields = {
						"title": htmllib.encoding(stringQ2B(htmllib.encoding(model.title)),'gb2312'),
						"content": htmllib.encoding(stringQ2B(htmllib.encoding(model.content)),'gb2312'),
						"name": pushitem.username,
						"password":pushitem.password
						}
				form_data = urllib.urlencode(form_fields)
				result = urlfetch.fetch(url='http://blog.163.com/common/targetgo.s',
							payload=form_data,
							method=urlfetch.POST,
							headers={'Content-Type': 'application/x-www-form-urlencoded'})

				if result.status_code == 200:
						return self.Get_True(model,pushitem)


				elif result.status_code == 500:
						logging.error('Push %s returned with status code 500.' %pushitem.pushurl)
						return False
				elif result.status_code == 404:
						logging.error('Error 404: Nothing found at %s.' % pushitem.pushurl)
						return False


			except Exception,data:
				return self.Get_False(model,pushitem,data)
				#break
		def Get_True(self,model,pushitem):
				"""
				if the result is True,we will do something to save db,
				and return the True
				"""
				pushitem.last_retrieved =datetime.now()
				pushitem.latest=model.date
				pushitem.put()
				return True

		def Get_False(self,model,pushitem,data=None):
				"""
				if the result is False,we will do something to save the result,and
				return the False
				"""
				logging.error('Could not push article %s ,and the push is restart now' % pushitem.pushurl)
				pushitem.last_retrieved =datetime.now()
				pushitem.latest=model.date
				if data:
						logging.info(data)
				pushitem.put()

		def Get_qzone(self,model,pushitem,**kwargs):
				try:
						message = mail.EmailMessage()
						message.sender = '%s@qq.com'% pushitem.username
						message.to = '%s@qzone.qq.com'% pushitem.username
						message.body =htmllib.encoding(stringQ2B(htmllib.encoding(model.content)),'gb2312')
						message.subject =htmllib.encoding(stringQ2B(htmllib.encoding(model.title)),'gb2312')
						message.send()
						return self.Get_True(model,pushitem)
				except Exception,data:
						return self.Get_False(model,pushitem,data)

		def Get_sina_msgs(self,model,pushitem,**kwargs):
				"""
				this method is used to get login to website,and put the content to the micro blog
				"""
				try:


					content='#%s# %s 详细内容请查看：%s'% (htmllib.encoding(stringQ2B(htmllib.encoding(model.title)),'utf-8'),
								htmllib.encoding(stringQ2B(htmllib.encoding(htmllib.Filter_html(model.excerpt))),'utf-8')[:100],
								str(model.fullurl))
					result=self.send_sina_msgs(pushitem.username,pushitem.password,content)
					if result:
						return self.Get_True(model,pushitem)
					else:
						return self.Get_False(model,pushitem)
				except Exception,data:
						return self.Get_False(model,pushitem,data)

		def Get_qq_msgs(self,model,pushitem,**kwargs):
				"""
				this method is used to get login to website,and put the content to the micro blog
				"""
				try:


					content='#%s# %s 详细内容请查看：%s'% (htmllib.encoding(stringQ2B(htmllib.encoding(model.title)),'utf-8'),
								htmllib.encoding(stringQ2B(htmllib.encoding(htmllib.Filter_html(model.excerpt))),'utf-8')[:100],
								str(model.fullurl))
					result=self.send_sina_msgs(pushitem.username,pushitem.password,content)
					if result:
						return self.Get_True(model,pushitem)
					else:
						return self.Get_False(model,pushitem)
				except Exception,data:
						return self.Get_False(model,pushitem,data)


		def make_cookie_header(self,cookie):
				ret = ""
				for val in cookie.values():
						ret+="%s=%s; "%(val.key, val.value)
				return ret

		def Make_dict(self,content):
				"""
				the content is a dict,but fetch.response is string,so
				we must change the string to dict
				"""
				tmpval=dict()
				content=content[1:][:-1].replace('"','')
				for val in content.split(','):
						tmpval.update({val.split(':')[0]:val.split(':')[1]})
				return tmpval

		def send_sina_msgs(self,username,password,msg):
			"""
			send sina msgs. use sina username, password.
			the msgs parameter is a message list, not a single string.
			"""
			try:
				result = urlfetch.fetch(url="https://login.sina.com.cn/sso/login.php?username=%s&password=%s&returntype=TEXT"%(username,password))
			except:
				return False
			if result.status_code == 200:
						tmpvalue=self.Make_dict(result.content)
						if not int(tmpvalue['retcode'])==0:
								return False
			else:
						return False
			cookie = Cookie.SimpleCookie(result.headers.get('set-cookie', ''))
			msg=unescape(msg)
			form_fields = {
			  "content": msg,
			}
			form_data = urllib.urlencode(form_fields)
			try:
				result = urlfetch.fetch(url="http://t.sina.com.cn/mblog/publish.php?rnd=0.5100760071072727",
								payload=form_data,
								method=urlfetch.POST,
								headers={'Referer':'http://t.sina.com.cn','Cookie' : self.make_cookie_header(cookie)})
			except:
						return False
			if result.status_code == 200:
						return True
			else:
						return False
