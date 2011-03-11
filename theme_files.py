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

import os,stat
import sys
import logging
import wsgiref.handlers
from mimetypes import types_map
from datetime import datetime, timedelta
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.ext.zipserve import *
sys.path.append('modules')
from model import g_blog

# {{{ Handlers

cwd = os.getcwd()
theme_path = os.path.join(cwd, 'themes')
file_modifieds={}

max_age = 72000000  #expires in 10 minutes
def Error404(handler):
	handler.response.set_status(404)
	html = template.render(os.path.join(cwd,'views/404.html'), {'error':404})
	handler.response.out.write(html)


class GetFile(webapp.RequestHandler):
	def Get_Memcache(self,key):
		result = memcache.get(key)
		if result is not None:
				#logging.info('load %s from memcache',key)
				return result,True
		else:
				return None,False

	def Add_Memcache(self,key,mfile,mime_type,fmtime):
			result=[mfile,mime_type,fmtime]
			memcache.add(key,result,time=720000)
			#logging.info('save %s to memcache',key)

	def get(self,prefix,name):
		request_path = self.request.path[8:]

		"""
		TODO this used for client cache
		"""

		if self.request.if_modified_since:
			mime_type=self.request.headers['Content-Type']
			self.response.headers['Content-Type'] = mime_type
			self.response.headers['Date'] = format_date(datetime.utcnow())
			self.response.headers['Last-Modified'] = self.request.headers['If-Modified-Since']
			Cache_expires(self.response, max_age,mime_type)
			self.response.set_status(304)
			#logging.info('the mime_type is %s,the fmtime is %s' %(mime_type,self.request.headers['If-Modified-Since']))
			self.response.clear()

		else:

			if g_blog.enable_memcache:
					result,checkmemcache=self.Get_Memcache(request_path)
			else:
					checkmemcache=False
			if not checkmemcache:
				"""
				TODO if the file not in memcache,so do this for file time,filepath.....
				"""
				server_path = os.path.normpath(os.path.join(cwd, 'themes', request_path))
				#logging.info(server_path)
				try:
					fstat=os.stat(server_path)
				except:
					#use zipfile
					theme_file=os.path.normpath(os.path.join(cwd, 'themes', prefix))
					if os.path.exists(theme_file+".zip"):
						#is file exist?
						fstat=os.stat(theme_file+".zip")
						zipdo=ZipHandler()
						zipdo.initialize(self.request,self.response)
						return zipdo.get(theme_file,name)
					else:
						Error404(self)
						return
				"""
				TODO the ext=file type,here is check the filetype and write the reponse head
				"""
				ext = os.path.splitext(server_path)[1]
				if types_map.has_key(ext):
						mime_type = types_map[ext]
				else:
						mime_type = 'application/octet-stream'
				fmtime=datetime.fromtimestamp(fstat[stat.ST_MTIME])
			else:
				"""
				TODO if the memcache is true,then do this ,get mfile,type and fmtime from memcache
				"""
				mfile=result[0]
				mime_type=result[1]
				fmtime=result[2]
			try:
				self.response.headers['Content-Type'] = mime_type
				self.response.headers['Last-Modified'] = format_date(fmtime)
				Cache_expires(self.response, max_age,mime_type)
				if checkmemcache:
						self.response.out.write(mfile)
				else:
						mfile=open(server_path, 'rb').read()
						self.Add_Memcache(request_path,mfile,mime_type,fmtime)
						self.response.out.write(mfile)

			except Exception, e:
				Error404(self)

class NotFound(webapp.RequestHandler):
	def get(self):
		 Error404(self)

#}}}

def format_date(dt):
	return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

def Cache_expires(response, seconds=0,mime_type=None, **kw):
	"""
	Set expiration on this request.  This sets the response to
	expire in the given seconds, and any other attributes are used
	for cache_control (e.g., private=True, etc).

	this function is modified from webob.Response
	it will be good if google.appengine.ext.webapp.Response inherits from this class...
	"""
	if seconds == 0:
		# To really expire something, you have to force a
		# bunch of these cache control attributes, and IE may
		# not pay attention to those still so we also set
		# Expires.
		response.headers['Cache-Control'] = 'max-age=0, must-revalidate, no-cache, no-store,public=true'
		response.headers['Expires'] = format_date(datetime.utcnow())
		if 'last-modified' not in self.headers:
			self.last_modified = format_date(datetime.utcnow())
		response.headers['Pragma'] = 'no-cache'
	else:
#TODO the images and js,css file are caching
		mimes=['text/css','application/x-javascript','image/png','image/jpg','image/jpeg','image/bmp','image/gif']
		if not mime_type in mimes:
				response.headers['Cache-Control'] = 'max-age=%d,public=true' % seconds
				response.headers['Expires'] = format_date(datetime.utcnow() + timedelta(seconds=seconds))
		else:
				response.headers['Cache-Control'] = 'max-age=72000000,public=true'
				response.headers['Expires'] = format_date(datetime.utcnow() + timedelta(seconds=72000000))


def main():
	application = webapp.WSGIApplication(
			[
				('/themes/[\\w\\-]+/templates/.*', NotFound),
				('/themes/(?P<prefix>[\\w\\-]+)/(?P<name>.+)', GetFile),
				('.*', NotFound),
				],
			debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
