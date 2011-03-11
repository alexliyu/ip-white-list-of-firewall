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
import cgi, os,sys,traceback
import wsgiref.handlers
##os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
##from django.conf import settings
##settings._target = None
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.utils.translation import check_for_language, activate, to_locale, get_language,gettext_lazy as _, ngettext
from django.conf import settings
settings._target = None

from google.appengine.ext.webapp import template, \
	WSGIApplication
from google.appengine.api import users
#import app.webapp as webapp2
from google.appengine.ext import db
from google.appengine.ext import zipserve
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.blobstore import blobstore
from datetime import datetime ,timedelta
import base64,random,math,zipfile
from django.utils import simplejson
import pickle
from base import *
from model import *
import urllib
from app.trackback import TrackBack
import xmlrpclib
from xmlrpclib import Fault
from time import sleep
from app import htmllib
from app.htmllib import getImageInfo

class Error404(BaseRequestHandler):
	#@printinfo
	def get(self,slug=None):
		self.render2('views/admin/404.html')

class setlanguage(BaseRequestHandler):
	def get(self):
		lang_code = self.param('language')
		next = self.param('next')
		if (not next) and os.environ.has_key('HTTP_REFERER'):
			next = os.environ['HTTP_REFERER']
		if not next:
			next = '/'
		os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
		from django.utils.translation import check_for_language, activate, to_locale, get_language
		from django.conf import settings
		settings._target = None

		if lang_code and check_for_language(lang_code):
			g_blog.language=lang_code
			activate(g_blog.language)
			g_blog.save()
		self.redirect(next)



##			if hasattr(request, 'session'):
##				request.session['django_language'] = lang_code
##			else:

##			cookiestr='django_language=%s;expires=%s;domain=%s;path=/'%( lang_code,
##					   (datetime.now()+timedelta(days=100)).strftime("%a, %d-%b-%Y %H:%M:%S GMT"),
##					   ''
##					   )
##			self.write(cookiestr)

			#self.response.headers.add_header('Set-Cookie', cookiestr)



class admin_do_action(BaseRequestHandler):
	@requires_admin
	def get(self,slug=None):
		try:
			func=getattr(self,'action_'+slug)
			if func and callable(func):
				func()
			else:
				self.render2('views/admin/error.html',{'message':_('This operate has not defined!')})
		except:
			 self.render2('views/admin/error.html',{'message':_('This operate has not defined!')})

	@requires_admin
	def post(self,slug=None):
		try:
			func=getattr(self,'action_'+slug)
			if func and callable(func):
				func()
			else:
				self.render2('views/admin/error.html',{'message':_('This operate has not defined!')})
		except:
			 self.render2('views/admin/error.html',{'message':_('This operate has not defined!')})

	def action_test(self):
		self.write(os.environ)

	def action_cacheclear(self):
		memcache.flush_all()
		self.write(_('"Cache cleared successful"'))

	def action_updatecomments(self):
		for entry in Entry.all():
			cnt=entry.comments().count()
			if cnt<>entry.commentcount:
				entry.commentcount=cnt
				entry.put()
		self.write(_('"All comments updated"'))

	def action_updatelink(self):
		link_format=self.param('linkfmt')
		if link_format:
			link_format=link_format.strip()
			g_blog.link_format=link_format
			g_blog.save()
			for entry in Entry.all():
					#if entry.link.startswith('/blog/')!=True or entry.link.startswith('/article/')!=True or entry.link.startswith('/download/')!=True:
						vals={'year':entry.date.year,'month':str(entry.date.month).zfill(2),'day':entry.date.day,
						'postname':entry.slug,'post_id':entry.post_id}
						if entry.slug:
							newlink=link_format%vals
						else:
							newlink=g_blog.link_format%vals

						newlink='/'+entry.entrytype+'/'+newlink
						if entry.link<>newlink:
							entry.link=newlink
							entry.put()
			self.write(_('"Link formated succeed"'))
		else:
			self.write(_('"Please input url format."'))

	def action_init_blog(self,slug=None):

		for com in Comment.all():
			com.delete()

		for entry in Entry.all():
			entry.Delete()

		g_blog.entrycount=0
		self.write(_('"Init has succeed."'))

	def action_update_tags(self,slug=None):
		for tag in Tag.all():
			tag.delete()
		for entry in Entry.all().filter('entrytype =','blog'):
			if entry.tags:
				for t in entry.tags:
					try:
						Tag.add(t)
					except:
						traceback.print_exc()

		self.write(_('"All tags for entry have been updated."'))


	def action_update_archives(self,slug=None):
		for archive in Archive.all():
			archive.delete()
		entries=Entry.all().filter('entrytype =','blog')

		archives={}


		for entry in entries:
			my = entry.date.strftime('%B %Y') # September-2008
			sy = entry.date.strftime('%Y') #2008
			sm = entry.date.strftime('%m') #09
			if archives.has_key(my):
				archive=archives[my]
				archive.entrycount+=1
			else:
				archive = Archive(monthyear=my,year=sy,month=sm,entrycount=1)
				archives[my]=archive

		for ar in archives.values():
			ar.put()

		self.write(_('"All entries have been updated."'))


	def action_trackback_ping(self):
		tbUrl=self.param('tbUrl')
		title=self.param('title')
		excerpt=self.param('excerpt')
		url=self.param('url')
		blog_name=self.param('blog_name')
		tb=TrackBack(tbUrl,title,excerpt,url,blog_name)
		tb.ping()

	def action_pingback_ping(self):
		"""Try to notify the server behind `target_uri` that `source_uri`
		points to `target_uri`.  If that fails an `PingbackError` is raised.
		"""
		source_uri=self.param('source')
		target_uri=self.param('target')
		try:
			response =urlfetch.fetch(target_uri)
		except:
			raise PingbackError(32)

		try:
			pingback_uri = response.headers['X-Pingback']
		except KeyError:
			_pingback_re = re.compile(r'<link rel="pingback" href="([^"]+)" ?/?>(?i)')
			match = _pingback_re.search(response.data)
			if match is None:
				raise PingbackError(33)
			pingback_uri =urldecode(match.group(1))

		rpc = xmlrpclib.ServerProxy(pingback_uri)
		try:
			return rpc.pingback.ping(source_uri, target_uri)
		except Fault, e:
			raise PingbackError(e.faultCode)
		except:
			raise PingbackError(32)




class admin_tools(BaseRequestHandler):
	def __init__(self):
		self.current="config"

	@requires_admin
	def get(self,slug=None):
		self.render2('views/admin/tools.html')


class admin_sitemap(BaseRequestHandler):
	def __init__(self):
		self.current="config"

	@requires_admin
	def get(self,slug=None):
		self.render2('views/admin/sitemap.html')


	@requires_admin
	def post(self):
		str_options= self.param('str_options').split(',')
		for name in str_options:
			value=self.param(name)
			setattr(g_blog,name,value)

		bool_options= self.param('bool_options').split(',')
		for name in bool_options:
			value=self.param(name)=='on'
			setattr(g_blog,name,value)

		int_options= self.param('int_options').split(',')
		for name in int_options:
			try:
				value=int( self.param(name))
				setattr(g_blog,name,value)
			except:
				pass
		float_options= self.param('float_options').split(',')
		for name in float_options:
			try:
				value=float( self.param(name))
				setattr(g_blog,name,value)
			except:
				pass


		g_blog.save()
		self.render2('views/admin/sitemap.html',{})

class admin_import(BaseRequestHandler):
	def __init__(self):
		self.current='config'

	@requires_admin
	def get(self,slug=None):
		gblog_init()
		self.render2('views/admin/import.html',{'importitems':
			self.blog.plugins.filter('is_import_plugin',True)})

##	def post(self):
##		try:
##			queue=taskqueue.Queue("import")
##			wpfile=self.param('wpfile')
##			#global imt
##			imt=import_wordpress(wpfile)
##			imt.parse()
##			memcache.set("imt",imt)
##
####			import_data=OptionSet.get_or_insert(key_name="import_data")
####			import_data.name="import_data"
####			import_data.bigvalue=pickle.dumps(imt)
####			import_data.put()
##
##			queue.add(taskqueue.Task( url="/admin/import_next"))
##			self.render2('views/admin/import.html',
##						{'postback':True})
##			return
##			memcache.set("import_info",{'count':len(imt.entries),'msg':'Begin import...','index':1})
##			#self.blog.import_info={'count':len(imt.entries),'msg':'Begin import...','index':1}
##			if imt.categories:
##				queue.add(taskqueue.Task( url="/admin/import_next",params={'cats': pickle.dumps(imt.categories),'index':1}))
##
##			return
##			index=0
##			if imt.entries:
##				for entry in imt.entries :
##					try:
##						index=index+1
##						queue.add(taskqueue.Task(url="/admin/import_next",params={'entry':pickle.dumps(entry),'index':index}))
##					except:
##						pass
##
##		except:
##			self.render2('views/admin/import.html',{'error':'import faiure.'})

class admin_setup(BaseRequestHandler):
	def __init__(self):
		self.current='config'

	@requires_admin
	def get(self,slug=None):
		vals={'themes':ThemeIterator()}
		self.render2('views/admin/setup.html',vals)

	@requires_admin
	def post(self):
		old_theme=g_blog.theme_name
		str_options= self.param('str_options').split(',')
		for name in str_options:
			value=self.param(name)
			setattr(g_blog,name,value)

		bool_options= self.param('bool_options').split(',')
		for name in bool_options:
			value=self.param(name)=='on'
			setattr(g_blog,name,value)

		int_options= self.param('int_options').split(',')
		for name in int_options:
			try:
				value=int( self.param(name))
				setattr(g_blog,name,value)
			except Exception,data:
				pass
		float_options= self.param('float_options').split(',')
		for name in float_options:
			try:
				value=float( self.param(name))
				setattr(g_blog,name,value)
			except:
				pass


		if old_theme !=g_blog.theme_name:
			g_blog.get_theme()


		g_blog.owner=self.login_user
		g_blog.author=g_blog.owner.nickname()
		#change type of the blog first page
		g_blog.blogtype=self.param('blogtype')
		if self.param('blobstore')=='True':
			g_blog.blobstore=True
		else:
			g_blog.blobstore=False
		g_blog.save()
		gblog_init()
		vals={'themes':ThemeIterator()}
		memcache.flush_all()
		self.render2('views/admin/setup.html',vals)
class Link_bookmarklet(BaseRequestHandler):
	def __init__(self):
		self.current='bookmarklet'

	@requires_admin
	def post(self):
		entry=None
		action='add'
		slug='blog'
		cats=Category.all().filter('media = ',slug)
		def mapit(cat):
			return {'name':cat.name,'slug':cat.slug,'select':entry and cat.key() in entry.categorie_keys}
		if self.param('title'):
				title=urllib.unquote(htmllib.decoding(self.param('title')))
				content=urllib.unquote(htmllib.decoding(self.param('snippet')))
				url=urllib.unquote(self.param('url'))
				vals={'action':action,'entry':entry,'entrytype':slug,'cats':map(mapit,cats),'title':title,'content':content,'url':url}
		else:
				vals={'action':action,'entry':entry,'entrytype':slug,'cats':map(mapit,cats)}
		self.render2('views/admin/entry.html',vals)

class admin_entry(BaseRequestHandler):
	def __init__(self):
		self.current='write'

	@requires_admin
	def get(self,slug='blog'):
		action=self.param("action")
		entry=None
		if action and  action=='edit':
				try:
					if self.param('key'):
							key=self.param('key')
					else:
							key=self.param('id')
					entry=Entry.get(key)

				except:
					pass
		else:
			action='add'
		cats=Category.all().filter('media = ',slug)
		def mapit(cat):
			return {'name':cat.name,'slug':cat.slug,'select':entry and cat.key() in entry.categorie_keys}
		if self.param('title'):
				title=urllib.unquote(htmllib.decoding(self.param('title')))
				excerpt=urllib.unquote(htmllib.decoding(self.param('excerpt')))
				url=urllib.unquote(self.param('url'))
				vals={'action':action,'entry':entry,'entrytype':slug,'cats':map(mapit,cats),'title':title,'content':excerpt,'url':url}
		else:
				vals={'action':action,'entry':entry,'entrytype':slug,'cats':map(mapit,cats)}
		self.render2('views/admin/entry.html',vals)

	@requires_admin
	def post(self,slug='post'):
		action=self.param("action")
		title=self.param("post_title")
		content=self.param('content')
		tags=self.param("tags")
		cats=self.request.get_all('cats')
		key=self.param('key')
		downloadurl=self.param('downloadurl')
		if len(self.param('downloadsize'))>0:
				downloadsize=float(self.param('downloadsize'))
		else:
				downloadsize=float(0)
		if self.param('publish')!='':
			published=True
		elif self.param('unpublish')!='':
			published=False
		else:
			published=self.param('published')=='True'

		allow_comment=self.parambool('allow_comment')
		allow_trackback=self.parambool('allow_trackback')
		entry_slug=self.param('slug')
		entry_parent=self.paramint('entry_parent')
		menu_order=self.paramint('menu_order')
		entry_excerpt=self.param('excerpt').replace('\n','<br>')
		password=self.param('password')
		sticky=self.parambool('sticky')
		imageurl=self.param('imageurl')
		is_external_page=self.parambool('is_external_page')
		target=self.param('target')
		external_page_address=self.param('external_page_address')

		def mapit(cat):
			return {'name':cat.name,'slug':cat.slug,'select':cat.slug in cats}
		catss=Category.all().filter('media = ',slug)
		vals={'action':action,'postback':True,'cats':catss,'entrytype':slug,
			  'cats':map(mapit,catss),
			  'entry':{ 'title':title,'content':content,'strtags':tags,'key':key,'published':published,
						 'allow_comment':allow_comment,
						 'allow_trackback':allow_trackback,
						'slug':entry_slug,
						'entry_parent':entry_parent,
						'excerpt':entry_excerpt,
						'menu_order':menu_order,
						'is_external_page':is_external_page,
						'target':target,
						'external_page_address':external_page_address,
						'password':password,
						'sticky':sticky,'imageurl':imageurl,'downloadurl':downloadurl}
			  }
		if not (title and (content or (is_external_page and external_page_address))):
			vals.update({'result':False, 'msg':_('Please input title and content.')})
			self.render2('views/admin/entry.html',vals)
		else:
			if action=='add':
				entry= Entry(title=title,content=content)
				entry.settags(tags)
				entry.entrytype=slug
				entry.slug=entry_slug.replace(" ","-")
				entry.entry_parent=entry_parent
				entry.menu_order=menu_order
				entry.excerpt=entry_excerpt
				entry.is_external_page=is_external_page
				entry.target=target
				entry.external_page_address=external_page_address
				newcates=[]
				entry.allow_comment=allow_comment
				entry.allow_trackback=allow_trackback
				entry.author=self.author.user
				entry.author_name=self.author.dispname
				entry.password=password
				entry.sticky=sticky
				entry.imageurl=imageurl
				entry.downloadurl=downloadurl
				entry.downloadsize=downloadsize
				if cats:

				   for cate in cats:
						c=Category.all().filter('slug =',cate)
						if c:
							newcates.append(c[0].key())
				entry.categorie_keys=newcates;

				entry.save(published)
				if published:
					smsg=_('Saved ok. <a href="%(link)s" target="_blank">View it now!</a>')
				else:
					smsg=_('Saved ok.')

				vals.update({'action':'edit','result':True,'msg':smsg%{'link':str(entry.link)},'entry':entry})
				self.render2('views/admin/entry.html',vals)
			elif action=='edit':
				try:
					entry=Entry.get(key)
					entry.title=title
					entry.content=content
					entry.slug=entry_slug.replace(' ','-')
					entry.entry_parent=entry_parent
					entry.menu_order=menu_order
					entry.excerpt=entry_excerpt
					entry.is_external_page=is_external_page
					entry.target=target
					entry.external_page_address=external_page_address
					entry.settags(tags)
					entry.author=self.author.user
					entry.author_name=self.author.dispname
					entry.password=password
					entry.sticky=sticky
					entry.imageurl=imageurl
					entry.downloadurl=downloadurl
					entry.downloadsize=downloadsize
					newcates=[]
					if cats:

						for cate in cats:
							c=Category.all().filter('slug =',cate)
							if c:
								newcates.append(c[0].key())
					entry.categorie_keys=newcates;
					entry.allow_comment=allow_comment
					entry.allow_trackback=allow_trackback

					entry.save(published)
					if published:
						try:
							smsg=_('Saved ok. <a href=%(link)s target=_blank>View it now!</a>')
						except Exception,data:
							logging.info('the error is %s',data)
					else:
						smsg=_('Saved ok.')
					vals.update({'result':True,'msg':smsg%{'link':str(entry.link)},'entry':entry})
					self.render2('views/admin/entry.html',vals)

				except Exception,data:
					#vals.update({'result':False,'msg':_('Error:Entry can''t been saved.')})
					#self.render2('views/admin/entry.html',vals)
					logging.info(data)

class admin_entries(BaseRequestHandler):
	@requires_admin
	def get(self,slug='post'):

		self.render2('views/admin/'+slug+'s.html',
		 {
		   'current':slug+'s'
		  }
		)

class admin_categories(BaseRequestHandler):
	@requires_admin
	def get(self,slug=None):
		try:
			"""
			the value of slug like page/2,so we use rsplit or split to get the number 2
			"""
			page_index=int(slug.rsplit('/')[1])

		except:
			page_index=1
		cats,pager=Pager(query=Category.allTops(),items_per_page=15).fetch(page_index,'categories')

		self.render2('views/admin/categories.html',
		 {
		   'current':'categories',
		   'cats':cats,
		   'pager':pager
		  }
		)

	@requires_admin
	def post(self,slug=None):
		try:
			linkcheck= self.request.get_all('checks')
			for key in linkcheck:

				cat=Category.get(key)
				cat.delete()
		finally:
			self.redirect('/admin/categories')

class admin_comments(BaseRequestHandler):
	@requires_admin
	def get(self,slug=None):
		try:
			page_index=int(self.param('page'))
		except:
			page_index=1



		cq=self.param('cq')
		cv=self.param('cv')
		if cq and cv:
			query=Comment.all().filter(cq+' =',cv).order('-date')
		else:
			query=Comment.all().order('-date')
		comments,pager=Pager(query=query,items_per_page=15).fetch(page_index)

		self.render2('views/admin/comments.html',
		 {
		   'current':'comments',
		   'comments':comments,
		   'pager':pager,
		   'cq':cq,
		   'cv':cv
		  }
		)

	@requires_admin
	def post(self,slug=None):
		try:
			linkcheck= self.request.get_all('checks')
			for key in linkcheck:

				comment=Comment.get(key)
				comment.delit()
		finally:
			self.redirect(self.request.uri)

class admin_links(BaseRequestHandler):
	@requires_admin
	def get(self,slug=None):
		self.render2('views/admin/links.html',
		 {
		  'current':'links',
		  'links':Link.all().filter('linktype =','blogroll')#.order('-createdate')
		  }
		)
	@requires_admin
	def post(self):
		linkcheck= self.request.get_all('linkcheck')
		for link_id in linkcheck:
			kid=int(link_id)
			link=Link.get_by_id(kid)
			link.delete()
		self.redirect('/admin/links')

class admin_link(BaseRequestHandler):
	@requires_admin
	def get(self,slug=None):
		action=self.param("action")
		vals={'current':'links'}
		if action and  action=='edit':
				try:
					action_id=int(self.param('id'))
					link=Link.get_by_id(action_id)
					vals.update({'link':link})
				except:
					pass
		else:
			action='add'
		vals.update({'action':action})

		self.render2('views/admin/link.html',vals)

	@requires_admin
	def post(self):
		action=self.param("action")
		name=self.param("link_name")
		url=self.param("link_url")
		comment = self.param("link_comment")

		vals={'action':action,'postback':True,'current':'links'}
		if not (name and url):
			vals.update({'result':False,'msg':_('Please input name and url.')})
			self.render2('views/admin/link.html',vals)
		else:
			if action=='add':
			   link= Link(linktext=name,href=url,linkcomment=comment)
			   link.put()
			   vals.update({'result':True,'msg':'Saved ok'})
			   self.render2('views/admin/link.html',vals)
			elif action=='edit':
				try:
					action_id=int(self.param('id'))
					link=Link.get_by_id(action_id)
					link.linktext=name
					link.href=url
					link.linkcomment = comment
					link.put()
					#goto link manage page
					self.redirect('/admin/links')

				except:
					vals.update({'result':False,'msg':_('Error:Link can''t been saved.')})
					self.render2('views/admin/link.html',vals)

class admin_category(BaseRequestHandler):
	def __init__(self):
		self.current='categories'

	@requires_admin
	def get(self,slug=None):
		action=self.param("action")
		key=self.param('key')
		category=None
		if action and  action=='edit':
				try:

					category=Category.get(key)

				except:
					pass
		else:
			action='add'
		vals={'action':action,'category':category,'key':key,'categories':[c for c in Category.all() if not category or c.key()!=category.key()]}
		self.render2('views/admin/category.html',vals)

	@requires_admin
	def post(self):
		def check(cate):
			parent=cate.parent_cat
			skey=cate.key()
			while parent:
				if parent.key()==skey:
					return False
				parent=parent.parent_cat
			return True

		action=self.param("action")
		name=self.param("name")
		slug=self.param("slug")
		parentkey=self.param('parentkey')
		key=self.param('key')
		media=self.param('ismedia')



		vals={'action':action,'postback':True}

		try:

				if action=='add':
					cat= Category(name=name,slug=slug,media=media)
					if not (name and slug):
						raise Exception(_('Please input name and slug.'))
					if parentkey:
						cat.parent_cat=Category.get(parentkey)

					cat.put()
					self.redirect('/admin/categories')

					#vals.update({'result':True,'msg':_('Saved ok')})
					#self.render2('views/admin/category.html',vals)
				elif action=='edit':

						cat=Category.get(key)
						cat.name=name
						cat.slug=slug
						cat.media=media
						if not (name and slug):
							raise Exception(_('Please input name and slug.'))
						if parentkey:
							cat.parent_cat=Category.get(parentkey)
							if not check(cat):
								raise Exception(_('A circle declaration found.'))
						else:
							cat.parent_cat=None
						cat.put()
						for entry in Entry.all().filter('categorie_keys = ', cat.key()):
								entry.entrytype=cat.media
								entry.put()
						self.redirect('/admin/categories')

		except Exception ,e :
			if cat.is_saved():
				cates=[c for c in Category.all() if c.key()!=cat.key()]
			else:
				cates= Category.all()

			vals.update({'result':False,'msg':e.message,'category':cat,'key':key,'categories':cates})
			self.render2('views/admin/category.html',vals)

class admin_status(BaseRequestHandler):
	@requires_admin
	def get(self):
		self.render2('views/admin/status.html',{'cache':memcache.get_stats(),'current':'status','environ':os.environ})
class admin_authors(BaseRequestHandler):
	@requires_admin
	def get(self):
		try:
			page_index=int(self.param('page'))
		except:
			page_index=1




		authors=User.all().filter('isAuthor =',True)
		entries,pager=Pager(query=authors,items_per_page=15).fetch(page_index)

		self.render2('views/admin/authors.html',
		 {
		   'current':'authors',
		   'authors':authors,
		   'pager':pager
		  }
		)


	@requires_admin
	def post(self,slug=None):
		try:
			linkcheck= self.request.get_all('checks')
			for key in linkcheck:

				author=User.get(key)
				author.delete()
		finally:
			self.redirect('/admin/authors')
class admin_author(BaseRequestHandler):
	def __init__(self):
		self.current='authors'

	@requires_admin
	def get(self,slug=None):
		action=self.param("action")
		author=None
		if action and  action=='edit':
				try:
					key=self.param('key')
					author=User.get(key)

				except:
					pass
		else:
			action='add'
		vals={'action':action,'author':author}
		self.render2('views/admin/author.html',vals)

	@requires_admin
	def post(self):
		action=self.param("action")
		name=self.param("name")
		slug=self.param("email")

		vals={'action':action,'postback':True}
		if not (name and slug):
			vals.update({'result':False,'msg':_('Please input dispname and email.')})
			self.render2('views/admin/author.html',vals)
		else:
			if action=='add':
			   author= User(dispname=name,email=slug	)
			   author.user=db.users.User(slug)
			   author.put()
			   vals.update({'result':True,'msg':'Saved ok'})
			   self.render2('views/admin/author.html',vals)
			elif action=='edit':
				try:
					key=self.param('key')
					author=User.get(key)
					author.dispname=name
					author.email=slug
					author.user=db.users.User(slug)
					author.put()
					if author.isadmin:
						g_blog.author=name
					self.redirect('/admin/authors')

				except:
					vals.update({'result':False,'msg':_('Error:Author can''t been saved.')})
					self.render2('views/admin/author.html',vals)
class admin_plugins(BaseRequestHandler):
	def __init__(self):
		self.current='plugins'

	@requires_admin
	def get(self,slug=None):
		vals={'plugins':self.blog.plugins}
		self.render2('views/admin/plugins.html',vals)

	@requires_admin
	def post(self):
		action=self.param("action")
		name=self.param("plugin")
		ret=self.param("return")
		self.blog.plugins.activate(name,action=="activate")
		if ret:
			self.redirect(ret)
		else:
			vals={'plugins':self.blog.plugins}
			self.render2('views/admin/plugins.html',vals)

class admin_plugins_action(BaseRequestHandler):
	def __init__(self):
		self.current='plugins'

	@requires_admin
	def get(self,slug=None):
		plugin=self.blog.plugins.getPluginByName(slug)
		if not plugin :
			self.error(404)
			return
		plugins=self.blog.plugins.filter('active',True)
		if not plugin.active:
			pcontent=_('''<div>Plugin '%(name)s' havn't actived!</div><br><form method="post" action="/admin/plugins?action=activate&amp;plugin=%(iname)s&amp;return=/admin/plugins/%(iname)s"><input type="submit" value="Activate Now"/></form>''')%{'name':plugin.name,'iname':plugin.iname}
			plugins.insert(0,plugin)
		else:
			pcontent=plugin.get(self)


		vals={'plugins':plugins,
			  'plugin':plugin,
			  'pcontent':pcontent}

		self.render2('views/admin/plugin_action.html',vals)

	@requires_admin
	def post(self,slug=None):

		plugin=self.blog.plugins.getPluginByName(slug)
		if not plugin :
			self.error(404)
			return
		plugins=self.blog.plugins.filter('active',True)
		if not plugin.active:
			pcontent=_('''<div>Plugin '%(name)s' havn't actived!</div><br><form method="post" action="/admin/plugins?action=activate&amp;plugin=%(iname)s&amp;return=/admin/plugins/%(iname)s"><input type="submit" value="Activate Now"/></form>''')%{'name':plugin.name,'iname':plugin.iname}
			plugins.insert(0,plugin)
		else:
			pcontent=plugin.post(self)


		vals={'plugins':plugins,
			  'plugin':plugin,
			  'pcontent':pcontent}

		self.render2('views/admin/plugin_action.html',vals)

class WpHandler(BaseRequestHandler):
	@requires_admin
	def get(self,tags=None):
		try:
			all=self.param('all')
		except:
			all=False

		if(all):
			entries = Entry.all().order('-date')
		else:
			str_date_begin=self.param('date_begin')
			str_date_end=self.param('date_end')
			try:
				date_begin=datetime.strptime(str_date_begin,"%Y-%m-%d")
				date_end=datetime.strptime(str_date_end,"%Y-%m-%d")
				entries = Entry.all().filter('date >=',date_begin).filter('date <',date_end).order('-date')
			except:
				self.render2('views/admin/404.html')
				return

		cates=Category.all()
		tags=Tag.all()

		self.response.headers['Content-Type'] = 'binary/octet-stream'#'application/atom+xml'
		self.render2('views/wordpress.xml',{'entries':entries,'cates':cates,'tags':tags})

class Upload(blobstore_handlers.BlobstoreUploadHandler,BaseRequestHandler):

	@requires_admin
	def get(self):
			if g_blog.blobstore:
					upload_url = blobstore.create_upload_url('/admin/upload')
					self.render2('views/admin/uploads.html',{'upload_url':upload_url})
			else:
					upload_url = '/admin/upload'
					self.render2('views/admin/blobuploads.html',{'upload_url':upload_url})

	def post(self):

			if g_blog.blobstore:
					result=UploadMethods().Addmedia_byt(self.get_uploads())

					self.redirect('/admin/upload')
			else:
					blobfile=self.param("Filedata")

					if not blobfile:
							return self.redirect('/admin/upload')
					ufile=self.request.params['Filedata']
					filename=ufile.filename
					mime =os.path.splitext(filename)[1][1:]
					description=self.param("description")
					name = self.param("name")
					url=self.param('url')
					image=UploadMethods().Addmedia_blob(filename,name,mime,blobfile,description,url)
					return


class TempUpload(blobstore_handlers.BlobstoreUploadHandler,BaseRequestHandler):

	def post(self):
		try:
			ordurl=self.param('ordurl')
			result=UploadMethods().FetchUploadModel(ordurl,self.get_uploads('file'))

			self.redirect('/robot/fetchimages')
		except:
			pass


class UploadEx(blobstore_handlers.BlobstoreUploadHandler,BaseRequestHandler):

	def get(self):
			mimes=['image/png','image/jpg','image/jpeg','image/bmp','image/gif']
			extstr=self.param('ext')
			ext=extstr.split('|')
			if g_blog.blobstore:
					if self.param('p'):
							self.write('''<html><body><script type="text/javascript" >parent.location.replace('/admin/uploadex?ext=image/jpg|image/png|image/jpeg|image/pjpeg|image/gif');</script></body></html>''')
					else:
							upload_url = blobstore.create_upload_url('/admin/uploadex')
							files=Media.all().filter('Album != ',None)
							if extstr!='*':
									files=files.filter('mtype IN',ext)
							self.render2('views/admin/upload.html',{'ext':extstr,'files':files})
			else:
					files=Media.all().filter('mtype IN ',mimes).order('-date')
					upload_url='/admin/uploadex'
					self.render2('views/admin/uploadex.html',{'ext':extstr,'files':files,'upload_url':upload_url})


	def post(self):
		if g_blog.blobstore:
				upload_files = self.get_uploads('userfile')
				blob_info = upload_files[0]
				media=UploadMethods().Addmedia(blob_info)
				self.redirect('/admin/uploadex?p=%s'% str(media.key()),permanent=True)
		else:
				ufile=self.request.params['userfile']
				name=ufile.filename
				mime =os.path.splitext(name)[1][1:]
				blobfile = self.param('userfile')
				media=UploadMethods().Addmedia_blob(name,name,mime,blobfile)
				self.write(simplejson.dumps({'name':media.name,'size':media.size,'id':str(media.key())}))


class UploadMain(BaseRequestHandler):
		def get(self):
				self.response.out.write('<html><body>')
				self.response.out.write("""<iframe frameborder="0" height="300" width="500"
									src="/admin/upserver/" scrolling="no" id="uploadserver" ></iframe>
									<div id="upshow"></div></body></html>""" )

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler,BaseRequestHandler):
		def post(self):
				name=self.param('name')
				description=self.param('description')
				album=self.param('albumkey')
				url=self.request.get('url')
				if g_blog.blobstore:

						upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
						blob_info = upload_files[0]
						media=AlbumMethods().AddPhoto(name,description,album,url,blob_info)
						self.redirect('/admin/upserver/?'+str(media.key()))
				else:
						blobfile=self.param("Filedata")
						if not blobfile:
								return self.redirect('/admin/uploads')
						ufile=self.request.params['Filedata']
						filename=ufile.filename
						mime =os.path.splitext(filename)[1][1:]
						description=self.param("description")
						name = self.param("name")
						url=self.param('url')
						media=AlbumMethods().AddPhoto(name,description,album,url,blobfile,mime,filename)

class UploadServer(BaseRequestHandler):
		def get(self):
				if g_blog.blobstore:
						upload_url = blobstore.create_upload_url('/admin/uploads')
						url=self.Checkurl(self.request.query_string)
						if not url:
								upshow=self.Nourl()
						else:
								imgurl=self.Geturl(url)
								upshow=self.Reurl(imgurl,url)
						self.response.out.write('''<html><head><script type="text/javascript">function window_onload() {var my=this.parent.document;var h = my.getElementById("albumkey").value;
									this.document.getElementById("albumkey").value=h;} %s''' %upshow)
						self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
						self.response.out.write("""<ul>标题:<input type="text" name="Name" id="Name"  vaule="标题" class="input" />
						相关网址:<input type="text" id="url" name="url" vaule="http://ccdm.tk" class="input"  />说明:</ul><ul><textarea name="description" id="description" cols="100" rows="10" wrap="virtual"></textarea></ul>
						<input name="albumkey" id="albumkey" type="hidden" value="{{albumkey}}" /><ul>上传照片: <input type="file" name="file"><input type="submit" name="submit" value="提交">  </ul></form>""")
				else:
						upload_url='/admin/uploads'
						self.render2('views/admin/blobuploadss.html', {'upload_url':upload_url})


		def Geturl(self,url):
				#realurl=[]
				imgserver='/serve/'
				simgserver='/sserve/?w=s&p='
				thebigimg=imgserver+url
				thesimg=simgserver+url
				#realurl=[thebigimg,thesimg]
				return thesimg

		def Nourl(self):
				thehtml='''</script><body onload="window_onload();">'''
				return thehtml

		def Reurl(self,imgurl,url):
				thehtml="""function setText(objId,x,newText) {
							with (this.parent.document) if (getElementById && ((obj=getElementById(objId))!=null))
							with (obj) innerHTML += unescape(newText);}</script></head>
					<body onload="setText('photo','','<li><img src=%s><br /><input type=checkbox name=deleteid value=%s /></li>  ');window_onload();">""" % (imgurl,url)
				return thehtml

		def Checkurl(self,url):
				theurl=url
				return theurl

class UploadMethods(BaseRequestHandler):
		def Addmedia(self,blob_info):
				media=Media()
				media.mtype=blob_info.content_type
				media.date=blob_info.creation
				media.filename=blob_info.filename
				media.size=blob_info.size
				media.filekey=blob_info.key()
				media.user=users.get_current_user()
				media.name=blob_info.filename
				media.put()
				return media

		def Addmedia_byt(self,uploads):
				try:
					for upload in uploads:
							result=db.run_in_transaction(self.UploadModel,upload)
					return True
				except:
					return False

		def Addmedia_blob(self,filename,name,mtype,blobfile,description=None,url=None):
				media=Media(key_name=str(hash(datetime.now())))
				mimes=['png','jpg','jpeg','bmp','gif']
				if not name:
					name=filename
				if mtype in mimes:
					media.mtype,media.width,media.height=getImageInfo(blobfile)
				else:
					media.mtype=mtype
				media.filename=filename
				media.size=len(blobfile)
				media.blobfile=blobfile
				media.user=users.get_current_user()
				media.name=name
				if description:
					media.description=description
				if url:
					media.url=url

				media.put()
				return media



		def UploadModel(self,upload,*args,**kwargs):

				media=Media(key_name=str(hash(upload.filename+str(upload.creation))))
				media.mtype=upload.content_type
				media.date=upload.creation
				media.filename=upload.filename
				media.size=upload.size
				media.filekey=upload.key()
				media.user=users.get_current_user()
				media.name=upload.filename
				media.put()
				return True

		def FetchUploadModel(self,oldurl,uploads,*args,**kwargs):
			try:
					from plugins.feedblog.feedmodel import Tempimages
					for upload in uploads:
						keyname=str(hash(oldurl))
						media=Media(key_name=keyname)
						media.mtype=upload.content_type
						media.date=upload.creation
						media.filename=upload.filename
						media.size=upload.size
						media.filekey=upload.key()
						media.user=users.get_current_user()
						media.name=upload.filename
						media.oldurl=oldurl
						media.put()

						tempmodel=Tempimages.get_by_key_name(keyname)
						tempmodel.stat=1
						tempmodel.put()
					return True
			except Exception,data:
				logging.info(data)

class AlbumMethods(BaseRequestHandler):
	def CreateAlbum(self,user,name='',password=''):
		'''创建相册'''
		album = Albums(albumname=name,albumpassword=password,albumauthor=user,tag=Albums().settags(htmllib.decoding(name)))
		album.Save()
		return True

	def GetAllAlbums(self):
		albums=Albums().GetAll()
		return albums

	def GetAlbum(self,id):
		return Albums().get_by_id(int(id))



	def DeleteAlbum(self,id):
		album = self.GetAlbum(int(id))
		if album is not None:
			album.Delete()



	def AddPhoto(self,name,description,album,url,blob_info,mime=None,filename=None):
		#TODO add the photo wite album
		if g_blog.blobstore:
				media=Media(key_name=str(hash(blob_info.creation+blob_info.filename)))
				media.mtype=blob_info.content_type
				media.date=blob_info.creation
				media.filename=blob_info.filename
				media.size=blob_info.size
				media.filekey=blob_info.key()
		else:
				media=Media(key_name=str(hash(str(datetime.now())+name)))
				media.filename=filename
				media.size=len(blob_info)
				media.blobfile=blob_info
				media.mtype,media.width,media.height=getImageInfo(blob_info)

		media.user=users.get_current_user()
		media.name=name
		media.Album = Albums().get(album).key()
		media.description = description
		media.url=url
		media.Save()
		return media

	def DeletePhoto(self,id):
		photo = Media().get(id)
		if photo is not None:
			photo.Album.photocount -=1
			photo.Album.put()
			photo.Delete()



	def GetPhoto(key):
		if g_blog.blobstore:
				blob_info = blobstore.BlobInfo.get(Media.get(key).filekey.key())
				blob_reader = blobstore.BlobReader(blob_info.key(),buffer_size=1048576)
				value = blob_reader.read()
		else:

				photo = Media().get(key)
				if photo is not None:
						value=photo.blobfile
		return value

class Admin_CreateAlbum(BaseRequestHandler):
    def get(self):
        self.render2('views/admin/album.html',{'albums':AlbumMethods().GetAllAlbums()})
    def post(self):
        AlbumMethods().CreateAlbum(self.login_user,self.request.get('albumname'),'')
        self.redirect('/admin/albums/',{})

class AdminEditAlbum(BaseRequestHandler):
    @requires_admin
    def get (self,id,*avg):
        album = AlbumMethods().GetAlbum(int(id))
        self.render2('views/admin/editalbum.html',{'album':album})

    @requires_admin
    def post(self,id,*avg):
		album = AlbumMethods().GetAlbum(int(self.param('albumid')))
		album.albumname = self.param('albumname')
		album.displayorder = int(self.param('displayorder'))
		album.tag=album.settags(htmllib.decoding(self.param('tag')))
		album.Save()
        #self.redirect('/admin/albums/')
		self.response.out.write('<script type="text/javascript">window.parent.location.reload();</script>')

class AdminDeleteAlbum(BaseRequestHandler):
    @requires_admin
    def get(self,id):
        AlbumMethods().DeleteAlbum(int(id))
        self.redirect('/admin/albums/')

class PhotoList(BaseRequestHandler):
    @requires_admin
    def get(self,id):
        album = AlbumMethods().GetAlbum(id)
        photos = album.Photos()
	albumkey=album.key()
        data = {'albums':AlbumMethods().GetAllAlbums(),'photos':photos,'albumid':id,'albumkey':albumkey}
        self.render2 ('views/admin/photos.html',data)

    def post(self,id):
        alid = int(self.request.get('alid'))
        if len(self.request.get('setcover')) > 0:
            pid = self.request.get('deleteid')
            album = AlbumMethods().GetAlbum(alid)
            album.coverid = str(pid)
            album.Save()
        else:
            ids =  self.request.get_all('deleteid')
            for i in ids:
                AlbumMethods().DeletePhoto(i)
        self.redirect('/admin/albums/'+str(alid)+'/')


class FileManager(BaseRequestHandler):

	def __init__(self):
		self.current='files'

	@requires_admin
	def get(self):
		self.render2('views/admin/filemanager.html',{})


class admin_main(BaseRequestHandler):
	@requires_admin
	def get(self,slug=None):
		if self.is_admin:
			self.redirect('/admin/setup')
		else:
			self.redirect('/admin/entries/blog')

class admin_ThemeEdit(BaseRequestHandler):
	@requires_admin
	def get(self,slug):
		zfile=zipfile.ZipFile(os.path.join(rootpath,"themes",slug+".zip"))
		newfile=zipfile.ZipFile('')
		for item  in zfile.infolist():
			self.write(item.filename+"<br>")

class Otherdoc(BaseRequestHandler):
	@requires_admin
	def get(self,slug=None):
		doc=OtherDoc().all()
		self.render2('views/admin/otherdoc.html',
		 {
		   'current':'otherdoc',
		   'otherdoc':doc
		  }
		)

	@requires_admin
	def post(self,slug=None):
		try:
			linkcheck= self.request.get_all('checks')
			for key in linkcheck:

				doc=OtherDoc.get(key)
				doc.delete()
		finally:
			self.redirect('/admin/otherdoc')


class admin_doc(BaseRequestHandler):
	def __init__(self):
		self.current='otherdoc'

	@requires_admin
	def get(self,slug=None):
		action=self.param("action")
		key=self.param('key')
		doc=None
		if action and  action=='edit':
				try:

					doc=OtherDoc.get(key)

				except:
					pass
		else:
			action='add'
		vals={'action':action,'doc':doc,'key':key,'otherdoc':OtherDoc.all()}
		self.render2('views/admin/doc.html',vals)

	@requires_admin
	def post(self):
		action=self.param("action")
		name=self.param("name")
		value=self.param("value")
		key=self.param('key')
		vals={'action':action,'postback':True}

		try:

				if action=='add':
					doc= OtherDoc(name=name,value=value)
					if not (name and value):
						raise Exception(_('Please input name and value.'))
					doc.put()
					self.redirect('/admin/otherdoc')
				elif action=='edit':

						doc=OtherDoc.get(key)
						doc.name=name
						doc.value=value
						if not (name and value):
							raise Exception(_('Please input name and value.'))
						doc.put()
						self.redirect('/admin/otherdoc')

		except Exception ,e :
			logging.info(e)
			vals.update({'result':False,'msg':e.message,'doc':doc,'key':key,'otherdoc':otherdoc})
			self.render2('views/admin/doc.html',vals)

class EditPhoto(BaseRequestHandler):
	def __init__(self):
		self.current='editphoto'

	@requires_admin
	def get(self,slug=None):
		action=self.param("action")
		key=self.param('edit')
		albumid=self.param('album')
		if (key and albumid):
				try:

					photo=Media().get(key)

				except:
					self.error(404)
		vals={'photo':photo,'key':key,'albumid':albumid}
		self.render2('views/admin/photo.html',vals)

	@requires_admin
	def post(self,slug=None):
		action=self.param("action")
		name=self.param("name")
		url=self.param("url")
		key=self.param('key')
		albumid=self.param('albumid')
		description=self.param('description')
		vals={'action':action,'postback':True}

		try:

				if action=='edit':

						photo=Media.get(key)
						photo.name=name
						photo.url=url
						photo.description=description
						if not name:
							raise Exception(_('Please input name.'))
						photo.put()
						self.redirect('/admin/albums/%s/'% albumid)

		except Exception ,e :
			logging.info(e)
			vals.update({'result':False,'msg':e.message,'photo':photo,'key':key})
			self.render2('views/admin/photo.html',vals)
class uploadtest(BaseRequestHandler):
		def get(self):
			upload_url = blobstore.create_upload_url('/admin/upload')
			self.render2('views/admin/test.html',{'upload_url':upload_url})
class AjaxList_server(BaseRequestHandler):
	@requires_admin
	def get(self):
		tplist=[]
		if self.param('action')=='save':
			result=Tojson().Getpost(self.request)
		elif self.param('action')=='add':
			result=Tojson().Getpost(self.request,model=Entry())
		else:
			try:
					page_index=int(self.param('page'))
			except:
					page_index=1
			if self.param('rows'):
					perpage=self.param('rows')
			else:
					perpage=20
			if self.param('model')=='media':
					tplist=['id','name','user','size','date','url','mtype','public','viewcount']
			elif self.param('model')=='blog':
					tplist=['id','date','title','author_name','commentcount','readtimes','published','entrytype','imageurl','allow_comment','link']
			elif self.param('model')=='article':
					tplist=['id','date','title','author_name','commentcount','readtimes','published','entrytype','imageurl','allow_comment','link']
			elif self.param('model')=='page':
					tplist=['id','date','title','author_name','commentcount','readtimes','published','entrytype','slug','is_external_page','external_page_address','link']
			elif self.param('model')=='download':
					tplist=['id','date','title','author_name','commentcount','readtimes','published','entrytype','slug','downloadurl','allow_comment','link']
			result=Tojson().Parseurl(self.request,perpage,tplist)
			#files,total,records=Tojson().Checkget(self.request,Media(),10)
			#files,links=AjaxPager(query=files,items_per_page=10).fetch(page_index)
			#myjson=Tojson().Getjson(tplist,total,page_index,10,files)
			self.write(result)
	@requires_admin
	def post(self):
			if self.param('oper')=='edit':
					#tmpmodel=self.Getmodel()
					result=Tojson().Getpost(self.request)
			elif self.param('oper')=='del':
					result=Tojson().Getpost(self.request)
			else:
					self.error(404)







class Tojson(BaseRequestHandler):
		def Getjson(self,tplist,total,ttotal,page,records,entries,*args):
			#try:
				tmplist=[]
				tmprows=dict()
				tmpdict=dict()
				mydata=dict({
					'total':total,
					'page':page,
					'records':records,
					'userdata': {'ttotal':ttotal},
					})
				for entry in entries:
						for i in tplist:
							if i=='id':
									tmpdict.update(dict(({i:str(entry.key())})))
							else:

									tmpdict.update(dict(({i:unicode((getattr(entry,i)))})))

						tmplist.append(tmpdict.copy())

						tmpdict.clear()

				tmprows=dict({'rows':tmplist})

				mydata.update(tmprows)

				return (simplejson.dumps(mydata))
			#except Exception,data:
			#	logging.info(data)

		def Checkget(self,tplist,model,perpage,rows,sidx,sord,page,**kwargs):

				if not perpage:
						perpage=10
				if sidx:
					try:
						if sord=='asc':
								result=model.order('-'+sidx)
						else:
								result=model.order(sidx)
					except:
						result=model
				else:
						result=model
				if rows:
						perpage=int(rows)
				if not page:
						page=1
				else:
						page=int(page)
				result,total,ttotal=AjaxPager(query=result,items_per_page=perpage).fetch(page)
				result= self.Getjson(tplist,total,ttotal,page,perpage,result)
				return result


		def Search(self,model,search,searchField,searchString,searchOper,**kwargs):
				oper=dict((['eq','='],\
						['ne','!='],\
						['lt','<'],\
						['le','<='],\
						['gt','>'],\
						['ge','>='],\
						['in','in'],\
						['ni','not in']
						))
				searchstring=searchString
				if not searchOper:
						searchOper='eq'
				if searchOper=='in' or searchOper=='ni':
						searchstring=searchString.split(',')

				if search:
						try:
							result=model.filter('%s %s '% (searchField,oper[searchOper]),searchstring)
						except:
							result=None
				else:
						result=None
				return result
				#/admin/test?_search=true&nd=1280085813109&rows=10&page=1&sidx=id&
				#sord=desc&searchField=name&searchString=5text.txt&searchOper=eq
				#if self.param('searchField') and self.param(searchString):

		def Parseurl(self,request,perpage,tplist):
				self.request=request
				kwargs=dict(self.request.GET)
				#TODO change the unicode to str
				kwargs=self.Getkeywords(kwargs)
				kwargs.update(search=kwargs.pop('_search'))
				result=db.Query()
				model=self.Getmodel(kwargs['model'])
				del kwargs['model']
				del kwargs['nd']
				if kwargs['search']=='true':
						result=self.Search(model,**kwargs)
				if result!=None:
						result=self.Checkget(tplist,model,perpage,**kwargs)
				else:
						result=None
				if result:
						return result
				else:
						return simplejson.dumps(['success:false'])


		def Getpost(self,request,**kwargs):
				self.request=request
				kwargs=dict(self.request.POST)
				kwargs=self.Getkeywords(kwargs)
#TODO the post like:{u'mtype': u'image/jpeg', u'viewcount': u'0',
#u'name': u'conew_20b7cd596824be1a2834f0bc.jpg',
#u'oper': u'edit', u'id': u'agpjZG0tc3lzdGVtchYLEgVNZWRpYSILLTE3OTA5OTE0ODUM'}
				if kwargs.has_key('model'):
						model=self.Getmodel(kwargs['model'])
						del kwargs['model']
				if kwargs['oper']=='edit':
						result=self.PostEdit(**kwargs)
				elif kwargs['oper']=='add':
						result=self.PostAdd(model,**kwargs)
				elif kwargs['oper']=='del':
						result=self.PostDel(**kwargs)
				if not result:
						return simplejson.dumps(['success:false'])
				else:
						return simplejson.dumps(['success:true'])

		def PostEdit(self,**kwargs):

				id=kwargs['id']
				if not id:
						return None
				del kwargs['id']
				del kwargs['oper']
				try:
						result=db.run_in_transaction(self.UpdateModel,db.Key(id),**kwargs)
				except:
						result=False
				return result

		def PostDel(self,id,**kwargs):
				#try:
					keys=id.split(',')
					#del kwargs['id']
					del kwargs['oper']
					for key in keys:
							result=db.run_in_transaction(self.DelModel,key,**kwargs)
							if result:
								g_blog.entrycount-=1
								g_blog.put()
					return result
				#except:
				#	return False

		def DelModel(self,key,**kwargs):
			#try:
				tmpmodel=db.get(key)
				result=tmpmodel.Delete()
				return result
			#except Exception,data:
			#	logging.error(data)
			#	return False

		def UpdateModel(self,key,**kwargs):
				tmpmodel=db.get(key)
				for order in kwargs:

					myorder=''
					if kwargs[order]=='true' or kwargs[order]=='false':
						if kwargs[order]=='true':
							myorder=True
						elif kwargs[order]=='false':
							myorder=False
						tmpmodel.__setattr__(order,myorder)
					elif order=='date' or order=='creatdate':
							myorder=datetime(kwargs[order])
							tmpmodel.__setattr__(order,myorder)
					else:
						mytype=type(getattr(tmpmodel,order))

						tmpmodel.__setattr__(order,mytype(kwargs[order]))
				db.put(tmpmodel)
				return True
		def Getmodel(self,model):
			if model in ['blog','article','download','page']:
					tmpmodel=Entry().all().filter('entrytype = ',model)
			elif model=='media':
					tmpmodel=Media().all()
			else:
				self.write(simplejson.dumps(['success:false']))
			return tmpmodel


class AjaxPager(object):

	def __init__(self, model=None,query=None, items_per_page=10):
		if model:
			self.query = model.all()
		else:
			self.query=query


		self.items_per_page = items_per_page

	def fetch(self, p,mode='blog'):
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

		return (results, n,max_offset)

class reinstall(BaseRequestHandler):
		def get(self):
				g_blog.media_per_page= 20
				g_blog.article_per_page= 20
				g_blog.album_per_page= 20
				g_blog.feedurl = '/feed'
				g_blog.blogurl = '/blog'
				g_blog.albumurl = '/album'
				g_blog.downloadurl = '/download'
				g_blog.articleurl = '/article'
				g_blog.put()
				for entry in Entry().all():
						if entry.entrytype=='post':
								entry.entrytype='blog'
								entry.put()
						elif entry.entrytype!='article':
								entry.entrytype='article'
								entry.put()
				for cat in Category().all():
						if cat.media==None or cat.media=='post':
								cat.media='article'
								cat.put()

				for tag in Tag().all():
						tag.tagtype='article'
						tag.put()




def main():
	webapp.template.register_template_library('filter')
	webapp.template.register_template_library('app.recurse')

	application = webapp.WSGIApplication(
					[
					('/admin/{0,1}',admin_main),
					('/admin/setup',admin_setup),
					('/admin/entries/(blog|page|article|download)',admin_entries),
					('/admin/Link_bookmarklet',Link_bookmarklet),
					('/admin/links',admin_links),
					('/admin/categories',admin_categories),
					('/admin/categories/(\S+)',admin_categories),
					('/admin/comments',admin_comments),
					('/admin/link',admin_link),
					('/admin/category',admin_category),
					#TODO /admin/(post|page|article|download),the (post|page|article|download)=slug
					('/admin/(blog|page|article|download)',admin_entry),
					('/admin/(blog|page|article|download)/',admin_entry),
					 ('/admin/status',admin_status),
					 ('/admin/authors',admin_authors),
					 ('/admin/author',admin_author),
					 ('/admin/import',admin_import),
					 ('/admin/tools',admin_tools),
					 ('/admin/plugins',admin_plugins),
					 ('/admin/plugins/(\w+)',admin_plugins_action),
					 ('/admin/sitemap',admin_sitemap),
					 ('/admin/export/cdm.xml',WpHandler),
					 ('/admin/do/(\w+)',admin_do_action),
					 ('/admin/lang',setlanguage),
					 ('/admin/theme/edit/(\w+)',admin_ThemeEdit),
					 ('/admin/albums/',Admin_CreateAlbum),
					 ('/admin/albums/deleteAlbum/(?P<id>[0-9]+)/',AdminDeleteAlbum),
					 ('/admin/albums/(?P<id>[0-9]+)/',PhotoList),
					 ('/admin/albums/edit/(?P<id>[0-9]+)/(.*)',AdminEditAlbum),
					 ('/admin/photo/(.*)',EditPhoto),
					 ('/admin/upload', Upload),
					 ('/admin/filemanager', FileManager),
					 ('/admin/otherdoc', Otherdoc),
					 ('/admin/doc', admin_doc),
					 ('/admin/uploadex', UploadEx),
					 ('/admin/upserver/.*', UploadServer),
					 ('/admin/uploads', UploadHandler),
					 ('/admin/tempupload', TempUpload),
					 ('/admin/uploadmain', UploadMain),
					 ('/admin/uploadtest', uploadtest),
					 ('/admin/ajaxlist', AjaxList_server),
					 ('/admin/reinstall',reinstall),
					 ('.*',Error404),
					 ],debug=True)
	g_blog.application=application
	g_blog.plugins.register_handlerlist(application)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
	main()
