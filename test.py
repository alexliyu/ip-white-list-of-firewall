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

import wsgiref.handlers
import xmlrpclib
from xmlrpclib import Fault
import sys
import cgi
import base64
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
import hashlib


class test(BaseRequestHandler):
		def get(self):
				#url='http://blog.163.com/common/targetgo.s'
				#form_fields = {
				#		"title": "Albert",
				#		"content": "Johnson",
				#		"name": "alexliyu",
				#		"password":"lovealex"
				#		}
				#form_data = urllib.urlencode(form_fields)
				#result = urlfetch.fetch(url=url,
				#			payload=form_data,
				#			method=urlfetch.POST,
				#			headers={'Content-Type': 'application/x-www-form-urlencoded'})
				#self.write (result.content)
				self.Get_qq_msgs('456','789','alexliyu2012@qq.com','lovewzl')

		def Get_qq_msgs(self,title,excerpt,username,password,**kwargs):
				"""
				this method is used to get login to website,and put the content to the micro blog
				"""



				content='#%s# %s 详细内容请查看：%s'% (htmllib.encoding(stringQ2B(htmllib.encoding(title)),'utf-8'),
								htmllib.encoding(stringQ2B(htmllib.encoding(htmllib.Filter_html(excerpt))),'utf-8')[:100],
								str('http://www.163.com'))
				result=self.send_sina_msgs(username,password,content)
				if result:
						logging.info('push sucessfull')
				else:
						logging.info('fail')


		def make_cookie_header(self,cookie):
				ret = ""
				for val in cookie.values():
						ret+="%s=%s; "%(val.key, val.value)
				return ret

		def make_cookie_header2(self,cookie):
				ret = ""
				for val in cookie.values():
						ret+="%s=%s; "%(val.split('=')[0], val.split('=')[1])
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

		def Make_cookie_dict(self,cookie):
				tmpval=dict()
				for val in cookie:
						tmpval.update({val.split('=')[0]:val.split('=')[1]})
				return tmpval

		def md5hash(self,str):
				return hashlib.md5(str).digest()
		def hex_md5hash(self,str):
				return hashlib.md5(str).hexdigest().upper()
		def md5hash_3(self,str):
				return self.hex_md5hash(self.md5hash(self.md5hash(str)))
		def EncodePasswordWithVerifyCode(self,pwd, verifyCode):
				return self.hex_md5hash(self.md5hash_3(pwd) + verifyCode.upper())

		def Get_qq_msg_val(self,username,password):
				verifyURL = 'http://ptlogin2.qq.com/check?uin=%s&appid=15000101'% (username)
				loginURL = 'http://ptlogin2.qq.com/login?'
				redirectURL = ''
				cookie = ''
				qqn = username
				md5Pass = ''
				verifyCode = ''
				result = urlfetch.fetch(url=verifyURL,method=urlfetch.GET,
						follow_redirects = False,headers={
						'Content-Type': 'application/x-www-form-urlencoded',
						'user-agent':'Mozilla/5.0 (Linux; U; Linux i686; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.4.2.80 Safari/525.13',
						},)
				cookie1 = Cookie.SimpleCookie(result.headers.get('set-cookie', ''))
				verifyCode=result.content[18:-3]
				loginURL += "u=%s&p="% username
				loginURL+=self.EncodePasswordWithVerifyCode(password,verifyCode)
				loginURL += "&verifycode="+verifyCode+"&aid=15000101&u1=http%3A%2F%2Fimgcache.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3fpara%3dizone&ptredirect=1&h=1&from_ui=1&fp=loginerroralert"
				result=urlfetch.fetch(url=loginURL,
						headers={'Referer':'http://t.qq.com',
						'Cookie' : self.make_cookie_header(cookie1),
						'Content-Type': 'application/x-www-form-urlencoded',
						'user-agent':'Mozilla/5.0 (Linux; U; Linux i686; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.4.2.80 Safari/525.13',
						},
						method=urlfetch.GET,
						follow_redirects = False,
				)
				setCookies = result.headers.get('set-cookie', '').split(';')
				cookie2 = ''
				cookie2+=setCookies[29]
				cookie2+=setCookies[7]
				cookie2+=setCookies[4]
				cookie2+=';'+setCookies[0]
				cookie2 = cookie2.replace(',', ';')
				cookie2 = cookie2[1:]
				callback_url = result.headers.get('location','http://imgcache.qq.com/qzone/v5/loginsucc.html?para=izone')
				result,cookie = self.do_redirect(callback_url, cookie2)

				return result,cookie


		def do_redirect(self,url, cookie):
				logging.info(url)
				result = urlfetch.fetch(
				url=url,
				headers={'Cookie':cookie,
					'Content-Type': 'application/x-www-form-urlencoded',
					'user-agent':'Mozilla/5.0 (Linux; U; Linux i686; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.4.2.80 Safari/525.13',},
					method=urlfetch.GET,
					follow_redirects = False,
					)
				logging.info(result.content)
				return result,cookie

		def send_sina_msgs(self,username,password,msg):
			"""
			send sina msgs. use sina username, password.
			the msgs parameter is a message list, not a single string.
			"""
			result,oldcookie=self.Get_qq_msg_val(username,password)
			cookie='%s;%s'% (result.headers.get('set-cookie', ''),oldcookie)

			logging.info(cookie)
			msg=unescape(msg)
			form_fields = {

			"uin":'939567050',
			"category":'öÈËÈÕ¼Ç',
			"title":'hhhhhhhhhhhhhhhhhhhhhhhh',
			"content":'hhhhhhhhhhhhhhhhhhhh',
			"html":'<p>hhhhhhhhhhhhhhhhhhhh<br></p>',
			"cb_autograph":'1',
			"topflag":'0',
			"needfeed":'0',
			"lp_type":'0',
			"g_tk":'1446347922',
			"scorr_20100723_":'http://qzs.qq.com/qzone/newblog/v5/editor.html|http://qzs.qq.com/qzone/newblog/v5/editor.html<http://user.qzone.qq.com/939567050/main',
			}
			form_data = urllib.urlencode(form_fields)
			try:
				result = urlfetch.fetch(url="http://b.qzone.qq.com/cgi-bin/blognew/blog_add",
								payload=form_data,
								method=urlfetch.POST,
								headers={'Referer':'http://imgcache.qq.com/qzone/v5/toolpages/fp_gbk.html',
								'Cookie' : cookie,
								'user-agent':'Mozilla/5.0 (Linux; U; Linux i686; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.4.2.80 Safari/525.13',

								},follow_redirects = False)
			except:
						return False
			logging.info(result.content)
			if result.status_code == 200:
						return True
			else:
						return False
def main():
	#webapp.template.register_template_library("filter")
	application = webapp.WSGIApplication(
			[
				('/test', test),

				],
			debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
