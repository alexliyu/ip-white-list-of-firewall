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
import os,logging
import re
from functools import wraps
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from django.utils import simplejson
##import app.webapp as webapp2
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.utils.translation import  activate
from django.template import TemplateDoesNotExist
from django.conf import settings
settings._target = None
#from model import g_blog,User
#activate(g_blog.language)
from google.appengine.api.labs import taskqueue
import wsgiref.handlers
from mimetypes import types_map
from datetime import datetime, timedelta
import urllib
import traceback
import cdm_template
from app.url import GetNewUrl
from google.appengine.ext.blobstore import blobstore


logging.info('module base reloaded')
def urldecode(value):
	"""
	TODO:use urllib.unquote to format the  string
	and return the result by utf-8 unicode
	"""
	return  urllib.unquote(urllib.unquote(value)).decode('utf8')

def urlencode(value):
	"""
	TODO:use urllib.unquote to format the  unicode
	and return the result by utf-8 string
	"""
	return urllib.quote(value.encode('utf8'))

def sid():
	"""
	TODO:return the value of datetime.now(),but by format %y%m%d%H%M%S
	"""
	now=datetime.datetime.now()
	return now.strftime('%y%m%d%H%M%S')+str(now.microsecond)


def requires_admin(method):
	"""
	TODO:this is a warp,
	used like:@requires_admin on the def.
	this mean:if you use this one on method,the method must be require admin
	"""
	@wraps(method)
	def wrapper(self, *args, **kwargs):
		if not self.is_login:
			self.redirect(users.create_login_url(self.request.uri))
			return
		elif not (self.is_admin
			or self.author):
			return self.error(403)
		else:
			return method(self, *args, **kwargs)
	return wrapper

def printinfo(method):
	"""
	TODO:this is a warp,it is usually used for debug,
	you can use it like this:
	@printinfo
	def xxxx(xxxx)
	"""
	@wraps(method)
	def wrapper(self, *args, **kwargs):
		print self #.__name__
		print dir(self)
		for x in self.__dict__:
			print x
		return method(self, *args, **kwargs)
	return wrapper
#only ajax methed allowed
def ajaxonly(method):
	"""
	TODO:this ia a warp,this used for the method,which we want to only use ajax.
	you can use like this:
	@ajaxonly
	def xxxx(xxxx)
	"""
	@wraps(method)
	def wrapper(self, *args, **kwargs):
		try:
			if self.request.headers["X-Requested-With"]!="XMLHttpRequest":
				self.error(404)
			else:
				return method(self, *args, **kwargs)
		except:
			self.error(404)
	return wrapper

def hostonly(method):
	"""
	TODO:this is a warp,only request from same host can passed
	"""
	@wraps(method)
	def wrapper(self, *args, **kwargs):
		if  self.request.headers['Referer'].startswith(os.environ['HTTP_HOST'],7):
			return method(self, *args, **kwargs)
		else:
			self.error(404)
	return wrapper

def format_date(dt):
	"""
	TODO:this method,return the datetime value of dt,which by format %a, %d %b %Y %H:%M:%S GMT
	"""
	return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

def cache(key="",time=3600,mime=None):
	"""
	TODO:this is a very important warp,because it control the cache of the app.
	key:the key of cache,this is the only mark of cache,so must be only one.if key is none,the default
	key is the url of this method
	time:the time for cache,default time is 3600s
	mime:the mime type of cache,like html,image/jpeg............if the default is None,the mime is application/octet-stream
	you can use this warp like this :
	@cache(key=xx,time=xxxx,mime=xxxx)
	def Methodname(value)
	"""
	def _decorate(method):
		def _wrapper(*args, **kwargs):
			from model import g_blog
			if not g_blog.enable_memcache:
				method(*args, **kwargs)
				return

			request=args[0].request
			response=args[0].response
			#arg[0] is BaseRequestHandler object
			if not Chk_cache(request,response,time,mime):
					skey=key+ request.path_qs
					html= memcache.get(skey)
					if html:
						logging.info('cache:%s,and method is %s',skey,method)
						response.last_modified =html[1]
						ilen=len(html)
						if ilen>=3:
							response.set_status(html[2])
						if ilen>=4:
							for skey,value in html[3].items():
								response.headers[skey]=value
						response.out.write(html[0])

					else:
						if 'last-modified' not in response.headers:
							response.last_modified = format_date(datetime.utcnow())
						else:
							response.last_modified=response.headers['last_modified']

						method(*args, **kwargs)
						if response.headers['X-AppEngine-BlobKey']:
								blob_info = blobstore.BlobInfo.get(response.headers['X-AppEngine-BlobKey'])
								result=blobstore.BlobReader(blob_info).read()
						else:
								result=response.out.getvalue()
						status_code = response._Response__status[0]
						#logging.debug("Cache:%s"%status_code)

						try:
							memcache.set(skey,(result,response.last_modified,status_code,response.headers),time)
							logging.info('write %s to cache,and the method is %s',skey,args)
						except:
							logging.info('the memcache is too big')

		return _wrapper
	return _decorate

def Chk_cache(request,response,seconds=0,mime_type=None):
	"""
	TODO:this method is used for check the request wether in the cache.
	if the request is in the client cache,return 304 to the client.
	if the request not in the client,but in the server memcache,then return the memcache value to the client.
	if all not,do the method,then return the result to the client,cache it in memchache and client cache.
	request:the request handler
	response:the response handler
	seconds:the cache time
	mime_type:the mime type
	"""
	request=request
	response=response
	if mime_type != None:
		mime_type = mime_type
	else:
		mime_type = 'application/octet-stream'
	response.headers['Content-Type'] = mime_type
	if request.if_modified_since and request.if_modified_since.replace(tzinfo=None) <= datetime.utcnow():

		response.headers['Date'] = format_date(datetime.utcnow())
		response.headers['Last-Modified'] = format_date(request.if_modified_since.replace(tzinfo=None))
		Cache_expires(request,response,seconds,mime_type)
		response.set_status(304)
		#logging.info('the mime_type is %s,the fmtime is %s' %(mime_type,request.headers['If-Modified-Since']))
		#response.clear()
		return True
	else:
		response.headers['Date'] = format_date(datetime.utcnow())
		response.headers['Last-Modified'] = format_date(datetime.utcnow())
		Cache_expires(request,response,seconds,mime_type)
		return False

def Cache_expires(request,response,seconds=0,mime_type=None, **kw):
	"""
	TODO:Caching the value method
	request:the request handler
	response:the response handler
	seconds:the cache time
	mime_type:the mime type
	"""
	if seconds==0:
		"""
		TODO:To really expire something, you have to force a
		bunch of these cache control attributes, and IE may
		not pay attention to those still so we also set
		Expires.
		"""
		response.headers['Cache-Control'] = 'max-age=0, must-revalidate, no-cache, no-store,public=true'
		response.headers['Expires'] = format_date(datetime.utcnow())
		response.headers['Pragma'] = 'no-cache'
	else:
		"""
		TODO:the images and js,css file are caching
		"""
		mimes=['text/css','application/x-javascript','image/png','image/jpg','image/jpeg','image/bmp','image/gif']
		if not mime_type in mimes:
				response.headers['Cache-Control'] = 'max-age=%d,public=true' % seconds
				response.headers['Expires'] = format_date(datetime.utcnow() + timedelta(seconds=seconds))
		else:
				response.headers['Cache-Control'] = 'max-age=7200000,public=true'
				response.headers['Expires'] = format_date(datetime.utcnow() + timedelta(seconds=7200000))

#-------------------------------------------------------------------------------
class PingbackError(Exception):
	"""
	TODO:Raised if the remote server caused an exception while pingbacking.
	This is not raised if the pingback function is unable to locate a
	remote server.
	"""

	_ = lambda x: x
	default_messages = {
		16: _(u'source URL does not exist'),
		17: _(u'The source URL does not contain a link to the target URL'),
		32: _(u'The specified target URL does not exist'),
		33: _(u'The specified target URL cannot be used as a target'),
		48: _(u'The pingback has already been registered'),
		49: _(u'Access Denied')
	}
	del _

	def __init__(self, fault_code, internal_message=None):
		Exception.__init__(self)
		self.fault_code = fault_code
		self._internal_message = internal_message

	def as_fault(self):
		"""
		TODO:Return the pingback errors XMLRPC fault.
		"""
		return Fault(self.fault_code, self.internal_message or
					 'unknown server error')

	@property
	def ignore_silently(self):
		"""
		TODO:If the error can be ignored silently.
		"""
		return self.fault_code in (17, 33, 48, 49)

	@property
	def means_missing(self):
		"""
		TODO:If the error means that the resource is missing or not
		accepting pingbacks.
		"""
		return self.fault_code in (32, 33)

	@property
	def internal_message(self):
		if self._internal_message is not None:
			return self._internal_message
		return self.default_messages.get(self.fault_code) or 'server error'

	@property
	def message(self):
		msg = self.default_messages.get(self.fault_code)
		if msg is not None:
			return _(msg)
		return _(u'An unknown server error (%s) occurred') % self.fault_code

class util:
	@classmethod
	def do_trackback(cls, tbUrl=None, title=None, excerpt=None, url=None, blog_name=None):
		taskqueue.add(url='/admin/do/trackback_ping',
			params={'tbUrl': tbUrl,'title':title,'excerpt':excerpt,'url':url,'blog_name':blog_name})

	#pingback ping
	@classmethod
	def do_pingback(cls,source_uri, target_uri):
		taskqueue.add(url='/admin/do/pingback_ping',
			params={'source': source_uri,'target':target_uri})



##cache variable

class Pager(object):
	"""
	TODO:This class is used for paging.
	model:Can be physical or Recordset
	query:the query
	items_per_page:The number of records per page,default number is 10
	"""

	def __init__(self, model=None,query=None, items_per_page=10):
		"""
		TODO:If the model parameters exist,
		self.query = model.all (). Otherwise,
		self.query = the query parameters
		"""
		if model:
			self.query = model.all()
		else:
			self.query=query

		self.items_per_page = items_per_page

	def fetch(self, p,mode='blog',index=False):
		"""
		TODO:According to parameters specified in the number of pages and num of per page,
		for get the Recordset.
		p:the number of pages
		mode:the entry.entrytype,default is blog
		"""
		if hasattr(self.query,'__len__'):
			max_offset=len(self.query)
		else:
			max_offset = self.query.count()
		n = max_offset / self.items_per_page
		if max_offset % self.items_per_page != 0:
			n += 1

		if p < 0 or p > n:
			p = 1
		offset = (p - 1) * self.items_per_page
		if hasattr(self.query,'fetch'):
			results = self.query.fetch(self.items_per_page, offset)
		else:
			results = self.query[offset:offset+self.items_per_page]

		prev=p-1
		next=p+1
		if next>n:next=0
		if prev <1:
			prev=None
		else:
			prev=GetNewUrl().Make_Page(mode,prev,index)

		if next >1:
			next=GetNewUrl().Make_Page(mode,next,index)
		else:
			next=None



		links = {'count':max_offset,'page_index':p,'prev': prev, 'next': next, 'last': n}

		return (results, links)



class BaseRequestHandler(webapp.RequestHandler):
	"""
	TODO:This system the most important class, which is one of the base class.
	for blog package,media package,wiki package,admin package.
	"""
	def __init__(self):
		self.current='home'

	def initialize(self, request, response):
		webapp.RequestHandler.initialize(self, request, response)
		os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
		from model import g_blog,User
		self.blog = g_blog
		self.login_user = users.get_current_user()
		self.is_login = (self.login_user != None)
		self.loginurl=users.create_login_url(self.request.uri)
		self.logouturl=users.create_logout_url(self.request.uri)
		self.is_admin = users.is_current_user_admin()

		if self.is_admin:
			self.auth = 'admin'
			self.author=User.all().filter('email =',self.login_user.email()).get()
			if not self.author:
				self.author=User(dispname=self.login_user.nickname(),email=self.login_user.email())
				self.author.isadmin=True
				self.author.user=self.login_user
				self.author.put()
		elif self.is_login:
			self.author=User.all().filter('email =',self.login_user.email()).get()
			if self.author:
				self.auth='author'
			else:
				self.auth = 'login'
		else:
			self.auth = 'guest'

		try:
			self.referer = self.request.headers['referer']
		except:
			self.referer = None



		self.template_vals = {'self':self,'blog':self.blog,'current':self.current}

	def __before__(self,*args,**kwargs):
		pass

	def __after__(self,*args,**kwargs):
		pass

	@cache(mime='text/html',time=360000)
	def error(self,errorcode,message='an error occured'):
		if errorcode == 404:
			message = 'Sorry, we were not able to find the requested page.  We have logged this error and will look into it.'
		elif errorcode == 403:
			message = 'Sorry, that page is reserved for administrators.  '
		elif errorcode == 500:
			message = "Sorry, the server encountered an error.  We have logged this error and will look into it."

		message+="<p><pre>"+traceback.format_exc()+"</pre><br></p>"
		self.template_vals.update( {'errorcode':errorcode,'message':message})






		if errorcode>0:
			self.response.set_status(errorcode)
		errorfile='error'+str(errorcode)+".html"
		try:
			content=cdm_template.render(self.blog.theme,errorfile, self.template_vals)
		except TemplateDoesNotExist:
			try:
				content=cdm_template.render(self.blog.theme,"error.html", self.template_vals)
			except TemplateDoesNotExist:
				content=cdm_template.render(self.blog.default_theme,"error.html", self.template_vals)
			except:
				content=message
		except:
			content=message
		self.response.out.write(content)

	def get_render(self,template_file,values):
		"""
		TODO:Helper method to render the template
		template_file:the template file name,but no '.html'
		values:the values for template
		"""
		template_file=template_file+".html"
		self.template_vals.update(values)

		try:
			html = cdm_template.render(self.blog.theme, template_file, self.template_vals)
		except TemplateDoesNotExist:
			html = cdm_template.render(self.blog.default_theme, template_file, self.template_vals)

		return html

	def render(self,template_file,values):
		"""
		TODO:Helper method to render the appropriate template
		"""
		#logging.info(template_file)
		html=self.get_render(template_file,values)
		self.response.out.write(html)

	@cache(mime='text/html')
	def wikirender(self,template_file,values):
		"""
		TODO:Helper method to render the wiki appropriate template,this one used the cache warp.
		so it is caching.
		"""
		template_file='wiki'+template_file
		self.template_vals.update(values)

		try:
			html = cdm_template.render(self.blog.theme, template_file, self.template_vals)
		except TemplateDoesNotExist:
			#sfile=getattr(self.blog.default_theme, template_file)
			html = cdm_template.render(self.blog.default_theme, template_file, self.template_vals)
		self.response.out.write(html)


	def message(self,msg,returl=None,title='Infomation'):
		"""
		TODO:Helper method to be a msg value for template
		"""
		self.render('msg',{'message':msg,'title':title,'returl':returl})

	def render2(self,template_file,template_vals={}):
		"""
		TODO:Helper method to render the appropriate template,but no cache
		"""

		self.template_vals.update(template_vals)
		path = os.path.join(self.blog.rootdir, template_file)
		self.response.out.write(template.render(path, self.template_vals))


	def param(self, name, **kw):
		"""
		TODO:Helper method to return the value of self.request.get(name)
		"""
		return self.request.get(name, **kw)

	def Getpage(self):
		"""
		TODO:Helper method to get the number of pages,which in the request url
		"""
		old=self.request.path_info
		if old.find('/page/')!=-1:

			return int(old.rsplit('/page/',1)[-1])
		else:
			return 1


	def Getslug(self,slug):
		"""
		TODO:Helper method to get the string after the /page/,which in the request url
		"""
		return urldecode(slug).split ('/page/')[0]

	def paramint(self, name, default=0):
		"""
		TODO:Helper method to get the request.get(name) by int type.
		"""
		try:
			return int(self.request.get(name))
		except:
			return default

	def parambool(self, name, default=False):
		"""
		TODO:Helper method to get the request.get(name) by boolean type.
		"""
		try:
			return self.request.get(name)=='on'
		except:
			return default


	def write(self, s):
		"""
		TODO:Helper method to response.out.write(s)
		"""
		self.response.out.write(s)



	def chk_login(self, redirect_url='/'):
		"""
		TODO:Check the request whether login
		"""
		if self.is_login:
			return True
		else:
			self.redirect(redirect_url)
			return False

	def chk_admin(self, redirect_url='/'):
		"""
		TODO:CHECK THE USER WHETHER ADMIN
		"""
		if self.is_admin:
			return True
		else:
			self.redirect(redirect_url)
			return False

	def Chk_cache(self,seconds=0,mime_type=None):
		"""
		TODO:Check for whether cached
		"""
		if mime_type != None:
			mime_type = mime_type
		else:
			mime_type = 'application/octet-stream'
		self.response.headers['Content-Type'] = mime_type
		if self.request.if_modified_since and self.request.if_modified_since.replace(tzinfo=None) <= datetime.utcnow():

			self.response.headers['Date'] = format_date(datetime.utcnow())
			self.response.headers['Last-Modified'] = format_date(self.request.if_modified_since.replace(tzinfo=None))
			self.Cache_expires(seconds,mime_type)
			self.response.set_status(304)
			self.response.clear()
			return True
		else:
			self.response.headers['Date'] = format_date(datetime.utcnow())
			self.response.headers['Last-Modified'] = format_date(datetime.utcnow())
			self.Cache_expires(seconds,mime_type)
			return False

	def Cache_expires(self, seconds=0,mime_type=None, **kw):
		if seconds==0:
			# To really expire something, you have to force a
			# bunch of these cache control attributes, and IE may
			# not pay attention to those still so we also set
			# Expires.
			self.response.headers['Cache-Control'] = 'max-age=0, must-revalidate, no-cache, no-store,public'
			self.response.headers['Expires'] = format_date(datetime.utcnow())
			self.response.headers['Pragma'] = 'no-cache'
		else:
	#TODO the images and js,css file are caching
			mimes=['text/css','application/x-javascript','image/png','image/jpg','image/jpeg','image/bmp','image/gif']
			if not mime_type in mimes:
				self.response.headers['Cache-Control'] = 'max-age=%d,public' % seconds
				self.response.headers['Expires'] = format_date(datetime.utcnow() + timedelta(seconds=seconds))
			else:
				self.response.headers['Cache-Control'] = 'max-age=7200000,public'
				self.response.headers['Expires'] = format_date(datetime.utcnow() + timedelta(seconds=7200000))

	def Getkeywords(self,kwargs):
			"""
			TODO:Finishing a dictionary object, if not a string key,
			remove from the dictionary.
			Finally, returns a new dictionary object.
			kwargs:the dict object
			"""
			if isinstance(kwargs,dict):
				for key, value in kwargs.items():
					if not isinstance(key, str):
						del kwargs[key]
						kwargs[str(key)] = value
				return kwargs
			else:
				return None

	def Post_data(self,model):
				"""
				TODO:Used to download files from the database output
				"""
				self.response.headers['Cache-Control'] = 'max-age=7200000,public'
				self.response.headers['Expires'] = 'Thu, 15 Apr 3010 20:00:00 GMT'
				self.response.headers['Content-Type'] = str(model.mtype)
				#self.response.headers['Content-Length']=str(len(model.blobfile))
				self.write(model.blobfile)
				self.response.headers.add_header('content-disposition',
								'attachment',
								 filename=str(model.filename))
