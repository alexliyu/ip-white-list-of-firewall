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

import os,logging,re
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.db import Model as DBModel
from google.appengine.api import memcache
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.ext.blobstore import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from datetime import datetime
import urllib, hashlib,urlparse
import zipfile,re,pickle,uuid
from app.url import GetNewUrl


#from base import *
logging.info('module base reloaded')

rootpath=os.path.dirname(__file__)

def vcache(key="",time=3600,first=""):
	def _decorate(method):
		def _wrapper(*args, **kwargs):
			if not g_blog.enable_memcache:
				return method(*args, **kwargs)
			tkey=key
			if tkey=="":
				if first!="":
					tkey=first
					targs=list(args[1:])
				else:
					targs=list(args)
				targs.extend(kwargs.values())
				for tmp in targs:
					tkey+=str(tmp)
			result = memcache.get(tkey)
			#logging.info('the key is %s,the result is %s' %(tkey,result))
			if result is None:
				result=method(*args, **kwargs)
				try:
					memcache.set(tkey,result,time)
				except Exception,data:
					logging.info('vcache is fail,the error is %s',data)
			return result

		return _wrapper
	return _decorate



class Theme:
	def __init__(self, name='default'):
		self.name = name
		self.mapping_cache = {}
		self.dir = '/themes/%s' % name
		self.viewdir=os.path.join(rootpath, 'view')
		self.server_dir = os.path.join(rootpath, 'themes',self.name)
		if os.path.exists(self.server_dir):
			self.isZip=False
		else:
			self.isZip=True
			self.server_dir =self.server_dir+".zip"
		#self.server_dir=os.path.join(self.server_dir,"templates")
		logging.debug('server_dir:%s'%self.server_dir)

	def __getattr__(self, name):
		if self.mapping_cache.has_key(name):
			return self.mapping_cache[name]
		else:

			path ="/".join((self.name,'templates', name + '.html'))
			logging.debug('path:%s'%path)
##			if not os.path.exists(path):
##				path = os.path.join(rootpath, 'themes', 'default', 'templates', name + '.html')
##				if not os.path.exists(path):
##					path = None
			self.mapping_cache[name]=path
			return path


class ThemeIterator:
	def __init__(self, theme_path='themes'):
		self.iterating = False
		self.theme_path = theme_path
		self.list = []

	def __iter__(self):
		return self

	def next(self):
		if not self.iterating:
			self.iterating = True
			self.list = os.listdir(self.theme_path)
			self.cursor = 0

		if self.cursor >= len(self.list):
			self.iterating = False
			raise StopIteration
		else:
			value = self.list[self.cursor]
			self.cursor += 1
			if value.endswith('.zip'):
				value=value[:-4]
			return value
			#return (str(value), unicode(value))

class LangIterator:
	def __init__(self,path='locale'):
		self.iterating = False
		self.path = path
		self.list = []
		for value in  os.listdir(self.path):
				if os.path.isdir(os.path.join(self.path,value)):
					if os.path.exists(os.path.join(self.path,value,'LC_MESSAGES')):
						try:
							lang=open(os.path.join(self.path,value,'language')).readline()
							self.list.append({'code':value,'lang':lang})
						except:
							self.list.append( {'code':value,'lang':value})

	def __iter__(self):
		return self

	def next(self):
		if not self.iterating:
			self.iterating = True
			self.cursor = 0

		if self.cursor >= len(self.list):
			self.iterating = False
			raise StopIteration
		else:
			value = self.list[self.cursor]
			self.cursor += 1
			return value

	def getlang(self,language):
		from django.utils.translation import  to_locale
		for item in self.list:
			if item['code']==language or item['code']==to_locale(language):
				return item
		return {'code':'en_US','lang':'English'}

class BaseModel(db.Model):
	def __init__(self, parent=None, key_name=None, _app=None, **kwds):
		self.__isdirty = False
		DBModel.__init__(self, parent=None, key_name=None, _app=None, **kwds)

	def __setattr__(self,attrname,value):
		"""
		DataStore api stores all prop values say "email" is stored in "_email" so
		we intercept the set attribute, see if it has changed, then check for an
		onchanged method for that property to call
		"""
		if (attrname.find('_') != 0):
			if hasattr(self,'_' + attrname):
				curval = getattr(self,'_' + attrname)
				if curval != value:
					self.__isdirty = True
					if hasattr(self,attrname + '_onchange'):
						getattr(self,attrname + '_onchange')(curval,value)

		DBModel.__setattr__(self,attrname,value)

	def PhotoUrl_s(self,thekey):
	    return 'http://%s%s?w=%s&p=%s' % (os.environ['HTTP_HOST'],'/sserve/','s',thekey)

class Cache(db.Model):
	cachekey = db.StringProperty(multiline=False)
	content = db.TextProperty()

class Blog(db.Model):
	owner = db.UserProperty()
	author=db.StringProperty(default='admin')
	rpcuser=db.StringProperty(default='admin')
	rpcpassword=db.StringProperty(default='')
	description = db.TextProperty()
	baseurl = db.StringProperty(multiline=False,default=None)
	urlpath = db.StringProperty(multiline=False)
	title = db.StringProperty(multiline=False,default='ChinaCDM')
	subtitle = db.StringProperty(multiline=False,default='This is a CDM SYSTEM.')
	entrycount = db.IntegerProperty(default=0)
	mediacount = db.IntegerProperty(default=0)
	albumcount = db.IntegerProperty(default=0)
	posts_per_page= db.IntegerProperty(default=10)
	media_per_page= db.IntegerProperty(default=10)
	article_per_page= db.IntegerProperty(default=10)
	album_per_page= db.IntegerProperty(default=10)
	feedurl = db.StringProperty(multiline=False,default='/feed')
	blogurl = db.StringProperty(multiline=False,default='/blog')
	albumurl = db.StringProperty(multiline=False,default='/album')
	downloadurl = db.StringProperty(multiline=False,default='/download')
	articleurl = db.StringProperty(multiline=False,default='/article')
	blogversion = db.StringProperty(multiline=False,default='0.30')
	theme_name = db.StringProperty(multiline=False,default='default')
	# the first page style
	blogtype = db.StringProperty(multiline=False,default='blog')

	blobstore=db.BooleanProperty(default=False)

	enable_memcache = db.BooleanProperty(default = False)
	link_format=db.StringProperty(multiline=False,default='%(year)s/%(month)s/%(day)s/%(post_id)s.html')
	comment_notify_mail=db.BooleanProperty(default=True)
	#评论顺序
	comments_order=db.IntegerProperty(default=0)
	#每页评论数
	comments_per_page=db.IntegerProperty(default=20)
	#comment check type 0-No 1-算术 2-验证码 3-客户端计算
	comment_check_type=db.IntegerProperty(default=1)

	blognotice=db.TextProperty(default='')

	domain=db.StringProperty()
	show_excerpt=db.BooleanProperty(default=True)
	version=0.501
	timedelta=db.FloatProperty(default=8.0)# hours
	language=db.StringProperty(default="en-us")

	sitemap_entries=db.IntegerProperty(default=30)
	sitemap_include_category=db.BooleanProperty(default=False)
	sitemap_include_tag=db.BooleanProperty(default=False)
	sitemap_ping=db.BooleanProperty(default=False)
	default_link_format=db.StringProperty(multiline=False,default='?p=%(post_id)s')
	default_theme=Theme("default")

	allow_pingback=db.BooleanProperty(default=False)
	allow_trackback=db.BooleanProperty(default=False)

	theme=None
	langs=None
	application=None




	def __init__(self,
			   parent=None,
			   key_name=None,
			   _app=None,
			   _from_entity=False,
			   **kwds):
		from cdm_plugin import Plugins
		self.plugins=Plugins(self)
		db.Model.__init__(self,parent,key_name,_app,_from_entity,**kwds)

	def tigger_filter(self,name,content,*arg1,**arg2):
		return self.plugins.tigger_filter(name,content,blog=self,*arg1,**arg2)

	def tigger_action(self,name,*arg1,**arg2):
	 	return self.plugins.tigger_action(name,blog=self,*arg1,**arg2)

	def tigger_urlmap(self,url,*arg1,**arg2):
		return self.plugins.tigger_urlmap(url,blog=self,*arg1,**arg2)

	def tigger_newurl(self,order,*args):
		return GetNewUrl().Make_newurl(order,*args)

	def tigger_adminurl(self,order,*args):
		return GetNewUrl().Make_adminurl(order,*args)

	def get_ziplist(self):
		return self.plugins.get_ziplist();

	def save(self):
		self.put()

	def initialsetup(self):
		self.title = 'Your Web Title'
		self.subtitle = 'Your Web Subtitle'

	def get_theme(self):
		self.theme= Theme(self.theme_name);
		return self.theme

	def get_langs(self):
		self.langs=LangIterator()
		return self.langs

	def cur_language(self):
		return self.get_langs().getlang(self.language)

	def rootpath(self):
		return rootpath

	@vcache("blog.hotposts")
	def hotposts(self):
		return Entry.all().filter('entrytype =','post').filter("published =", True).order('-readtimes').fetch(8)

	@vcache("blog.recentposts")
	def recentposts(self):
		return Entry.all().filter('entrytype =','post').filter("published =", True).order('-date').fetch(8)

	@vcache("blog.postscount")
	def postscount(self):
		return Entry.all().filter('entrytype =','blog').filter("published =", True).order('-date').count()

	@vcache("blog.downloadscount")
	def downloadscount(self):
		return Entry.all().filter('entrytype =','download').filter("published =", True).order('-date').count()

	@vcache("blog.articlescount")
	def articlescount(self):
		return Entry.all().filter('entrytype =','article').filter("published =", True).order('-date').count()


class Category(db.Model):
	uid=db.IntegerProperty()
	name=db.StringProperty(multiline=False)
	slug=db.StringProperty(multiline=False)
	parent_cat=db.SelfReferenceProperty()
	"""
	TODO is media files?
	"""
	media=db.StringProperty(multiline=False,default='blog')
	"""
	TODO:post_count is the article count of this category,
	every day update once in corn.yaml
	"""
	post_count=db.IntegerProperty(default=0)

	"""
	TODO the etype is used for entrytype,
	because the category have the same name,but belong to diffent type
	"""
	def posts(self,etype='blog'):
			return Entry.all().filter('entrytype = ',etype).filter("published =", True).filter('categorie_keys =',self).order('-date')

	@property
	def count(self):
		"""
		TODO:this method is used for get the count of category
		self.posts:this method is used for get entry of category,
		but is not allow to more than 1000 in gae,so we used list type,
		and len to get the count of entries.
		memcache:used to save the result of count to the memcache,let system to fast
		"""
		if memcache.get(self.slug+'count'):
				return memcache.get(self.slug+'count')
		else:
				#ccount=len(list(self.posts()))
				count=self.post_count
				memcache.set(self.slug+'count',count,72000)
				return count
	@property
	def Dcount(self):
		"""
		do not use this,i will cut this in next.
		now,you can use count,that can work well
		"""
		if memcache.get(self.slug+'count'):
				return memcache.get(self.slug+'count')
		else:
				count=self.post_count
				memcache.set(self.slug+'count',count,72000)
				return count
	@property
	def Acount(self):
		"""
		do not use this,i will cut this in next.
		now,you can use count,that can work well
		"""
		if memcache.get(self.slug+'count'):
				return memcache.get(self.slug+'count')
		else:
				count=self.post_count
				memcache.set(self.slug+'count',count,72000)
				return count

	def Update_count(self):
		count=len(list(self.posts(etype=self.media)))
		self.post_count=count
		self.put()

	def put(self):
		db.Model.put(self)
		g_blog.tigger_action("save_category",self)

	def delete(self):
		for entry in Entry.all().filter('categorie_keys =',self):
			entry.categorie_keys.remove(self.key())
			entry.put()
		db.Model.delete(self)
		g_blog.tigger_action("delete_category",self)

	def ID(self):
		try:
			id=self.key().id()
			if id:
				return id
		except:
			pass

		if self.uid :
			return self.uid
		else:
			#旧版本Category没有ID,为了与wordpress兼容
			from random import randint
			uid=randint(0,99999999)
			cate=Category.all().filter('uid =',uid).get()
			while cate:
				uid=randint(0,99999999)
				cate=Category.all().filter('uid =',uid).get()
			self.uid=uid
			print uid
			self.put()
			return uid

	@classmethod
	def get_from_id(cls,id):
		cate=Category.get_by_id(id)
		if cate:
			return cate
		else:
			cate=Category.all().filter('uid =',id).get()
			return cate

	@property
	def children(self):
		key=self.key()
		return [c for c in Category.all().filter('parent_cat =',self)]


	@classmethod
	def allTops(self):
		return [c for c in Category.all() if not c.parent_cat]

	def Link_url(self):
			"""
			like entry.Link_url.
			this is also a function to get the url
			"""
			linkurl=g_blog.tigger_adminurl('category',self.media,self.slug)
			return linkurl
	@classmethod
	@vcache(time=360000)
	def Get_category(self,mode='all'):
			if mode=='all':
				return Category.all()
			else:
				return Category.all().filter('media = ',mode)

class Archive(db.Model):
	monthyear = db.StringProperty(multiline=False)
	year = db.StringProperty(multiline=False)
	month = db.StringProperty(multiline=False)
	entrycount = db.IntegerProperty(default=0)
	date = db.DateTimeProperty(auto_now_add=True)

	def Link_url(self):
			#linkurl='/%s/%s'% (self.year,self.month)
			linkurl=g_blog.tigger_adminurl('archive',self.year,self.month)
			return linkurl

	@classmethod
	@vcache(key='get_archive',time=360000)
	def Get_archive(self):
			return Archive.all().order('-year').order('-month').fetch(12)

class Tag(db.Model):
	tag = db.StringProperty(multiline=False)
	tagcount = db.IntegerProperty(default=0)
	tagtype =db.StringProperty(default='blog',multiline=False)

	@classmethod
	@vcache(key='get_tag',time=360000)
	def Get_tag(self):
		return Tag.all()

	@property
	def posts(self):
		return Entry.all('entrytype =','post').filter("published =", True).filter('tags =',self)
	@property
	def Tagurl(self):
		if 'album' in self.tagtype:
				tagurl=g_blog.tigger_adminurl('albumtag',self.tag)
		else:
				tagurl=g_blog.tigger_adminurl('tag',self.tag)
		return tagurl
	@classmethod
	def add(cls,value,tagtype='blog'):
		if value:
			tag= Tag.get_by_key_name(value)
			if not tag:
				tag=Tag(key_name=value)
				tag.tag=value
#TODO the tagtype is used for choice the type of tag
			if not tagtype in tag.tagtype:
				tag.tagtype=tag.tagtype+','+tagtype

			tag.tagcount+=1
			tag.put()
			return tag
		else:
			return None

	@classmethod
	def remove(cls,value):
		if value:
			tag= Tag.get_by_key_name(value)
			if tag:
				if tag.tagcount>1:
					tag.tagcount-=1
				else:
					tag.delete()

	@vcache('tag.Gettags')
	def Gettags(self):
			try:
				tags=[]
				for tag in Tag.all().filter('tagtype != ','album'):
						for i in tag.tagtype.split(','):
								if i == 'blog' or i=='article' or i=='download':
										tags.append(tag)
										continue
				return tags
			except Exception,data:
				logging.info(data)
#TODO THE MIME TYPE OF THE MEDIA FILES
class Mime(db.Model):
	mime = db.StringProperty(multiline=False)
	mimecount = db.IntegerProperty(default=0)
#TODO POST THE MEDIA FILES OF THIS MIME TYPE
	@property
	def posts(self):
		return Media.all('public =',True).filter('mtype =',self)
#TODO ADD THE NEW MIME TYPE
	@classmethod
	def add(cls,value):
		if value:
			mime= Mime.get_by_key_name(value)
			if not mime:
				mime=Mime(key_name=value)
				mime.mime=value

			mime.mimecount+=1
			mime.put()
			return mime
		else:
			return None
#TODO REMOVE THE TYPE OF MIME
	@classmethod
	def remove(cls,value):
		if value:
			mime= Mime.get_by_key_name(value)
			if mime:
				if mime.mimecount>1:
					mime.mimecount-=1
				else:
					mime.delete()



class Link(db.Model):
	href = db.StringProperty(multiline=False,default='')
	linktype = db.StringProperty(multiline=False,default='blogroll')
	linktext = db.StringProperty(multiline=False,default='')
	linkcomment = db.StringProperty(multiline=False,default='')
	createdate=db.DateTimeProperty(auto_now=True)

	@property
	def get_icon_url(self):
		"get ico url of the wetsite"
		ico_path = '/favicon.ico'
		ix = self.href.find('/',len('http://') )
		return (ix>0 and self.href[:ix] or self.href ) + ico_path

	def put(self):
		db.Model.put(self)
		g_blog.tigger_action("save_link",self)


	def delete(self):
		db.Model.delete(self)
		g_blog.tigger_action("delete_link",self)

	@classmethod
	@vcache(key='get_blogroll',time=360000)
	def Get_blogroll(self):
		return Link.all().filter('linktype =','blogroll')

class Entry(BaseModel):
	author = db.UserProperty()
	author_name = db.StringProperty()
	published = db.BooleanProperty(default=False)
	content = db.TextProperty(default='')
	readtimes = db.IntegerProperty(default=0)
	title = db.StringProperty(multiline=False,default='')
	date = db.DateTimeProperty(auto_now_add=True)
	mod_date = db.DateTimeProperty(auto_now_add=True)
	tags = db.StringListProperty()
	categorie_keys=db.ListProperty(db.Key)
	slug = db.StringProperty(multiline=False,default='')
	link= db.StringProperty(multiline=False,default='')
	monthyear = db.StringProperty(multiline=False)
	entrytype = db.StringProperty(multiline=False,default='post',choices=[
		'post','page','download','article','blog'])
	entry_parent=db.IntegerProperty(default=0)#When level=0 show on main menu.
	menu_order=db.IntegerProperty(default=0)
	commentcount = db.IntegerProperty(default=0)

	allow_comment = db.BooleanProperty(default=True) #allow comment
	#allow_pingback=db.BooleanProperty(default=False)
	allow_trackback=db.BooleanProperty(default=True)
	password=db.StringProperty()

	#compatible with wordpress
	is_wp=db.BooleanProperty(default=False)
	post_id= db.IntegerProperty()
	excerpt=db.TextProperty(default='')

	#external page
	is_external_page=db.BooleanProperty(default=False)
	target=db.StringProperty(default="_self")
	external_page_address=db.StringProperty()

	#keep in top
	sticky=db.BooleanProperty(default=False)
	#the images to show
	imageurl=db.StringProperty(default=None)
	downloadurl=db.StringProperty(default=None)
	downloadsize=db.FloatProperty(default=0.00)

	postname=''
	_relatepost=None

	@property
	def content_excerpt(self):
		return self.get_content_excerpt(_('..more').decode('utf8'))


	def get_author_user(self):
		if not self.author:
			self.author=g_blog.owner
		return User.all().filter('email =',self.author.email()).get()

	def get_content_excerpt(self,more='..more'):
		if g_blog.show_excerpt:
			if self.excerpt:
				return self.excerpt+' <a href="%s">%s</a>'%(self.link,more)
			else:
				sc=self.content.split('<!--more-->')
				if len(sc)>1:
					return sc[0]+u' <a href="%s">%s</a>'%(self.link,more)
				else:
					return sc[0]
		else:
			return self.content

	def slug_onchange(self,curval,newval):
		if not (curval==newval):
			self.setpostname(newval)

	@classmethod
	@vcache(key='get_mpages')
	def Get_mpages(self):
		return Entry.all().filter('entrytype =','page')\
				.filter('published =',True)\
				.filter('entry_parent =',0)\
				.order('menu_order')

	def setpostname(self,newval):
			 #check and fix double slug
			if newval:
				slugcount=Entry.all()\
						  .filter('entrytype',self.entrytype)\
						  .filter('date <',self.date)\
						  .filter('slug =',newval)\
						  .filter('published',True)\
						  .count()
				if slugcount>0:
					self.postname=newval+str(slugcount)
				else:
					self.postname=newval
			else:
				self.postname=""




	@property
	def fullurl(self):
		return g_blog.baseurl+self.link;

	@property
	def categories(self):
		try:
			return db.get(self.categorie_keys)
		except:
			return []

	@property
	def post_status(self):
		return  self.published and 'publish' or 'draft'

	def settags(self,values):
		if not values:tags=[]
		if type(values)==type([]):
			tags=values
		else:
			tags=values.split(',')



		if not self.tags:
			removelist=[]
			addlist=tags
		else:
			#search different  tags
			removelist=[n for n in self.tags if n not in tags]
			addlist=[n for n in tags if n not in self.tags]
		for v in removelist:
			Tag.remove(v)
		for v in addlist:
			Tag.add(v)
		self.tags=tags

	def get_comments_by_page(self,index,psize):
		"""
		TODO:this method is used for get the comments
		index:the page number
		psize:the per page number
		"""
		return self.comments().order('-date').fetch(psize,offset = (index-1) * psize)

	@property
	def strtags(self):
		return ','.join(self.tags)

	@property
	def edit_url(self):
		return g_blog.tigger_adminurl('editentry',self.entrytype,self.entrytype,self.key())

	def Link_url(self):
		"""
		this is the entry url funciton,so if you want get a entry url,you can use this.
		not use entry.link.
		"""
		linkurl=''
		if self.link[0:1]=='/':
			linkurl=self.link
		else:
			#linkurl='/%s/%s'% (self.entrytype,self.link)
			try:
					linkurl=g_blog.tigger_adminurl('entrylink',self.entrytype,self.link)
			except Exception,data:
					logging.info(data)
		return linkurl

	def comments(self):
		if g_blog.comments_order:
			return Comment.all().filter('entry =',self).order('-date')
		else:
			return Comment.all().filter('entry =',self).order('date')

	def commentsTops(self):
		return [c for c  in self.comments() if c.parent_key()==None]

	def delete_comments(self):
		cmts = Comment.all().ancestor(self).filter('entry =',self)
		for comment in cmts:
			comment.delete()
		self.commentcount = 0

	def update_archive(self,cnt=1):
		"""Checks to see if there is a month-year entry for the
		month of current blog, if not creates it and increments count"""
		my = self.date.strftime('%B %Y') # September-2008
		sy = self.date.strftime('%Y') #2008
		sm = self.date.strftime('%m') #09


		archive = Archive.all().ancestor(self).filter('monthyear',my).get()
		if self.entrytype == 'post':
			if not archive:
				archive = Archive(monthyear=my,year=sy,month=sm,entrycount=1)
				self.monthyear = my
				archive.put()
			else:
				# ratchet up the count
				archive.entrycount += cnt
				archive.put()
		#g_blog.entrycount+=cnt
		#g_blog.put()


	def save(self,is_publish=False):
		"""
		Use this instead of self.put(), as we do some other work here
		@is_pub:Check if need publish id
		"""
		g_blog.tigger_action("pre_save_post",self,is_publish)
		my = self.date.strftime('%B %Y') # September 2008
		self.monthyear = my
		old_publish=self.published
		self.mod_date=datetime.now()

		if is_publish:
			if not self.is_wp:
				self.put()
				self.post_id=self.key().id()

			#fix for old version
			if not self.postname:
				self.setpostname(self.slug)


			vals={'year':self.date.year,'month':str(self.date.month).zfill(2),'day':self.date.day,
				'postname':self.postname,'post_id':self.post_id}


			if self.entrytype=='page':
				if self.slug:
					self.link='/page/'+self.postname
				else:
					#use external page address as link
					if self.is_external_page:
						self.link=self.external_page_address
					else:
						self.link='/page/'+g_blog.default_link_format%vals
			else:
				if g_blog.link_format and self.postname:
					self.link='/'+self.entrytype+'/'+g_blog.link_format.strip()%vals
				else:
					self.link='/'+self.entrytype+'/'+g_blog.default_link_format%vals


		self.published=is_publish
		self.put()

		if is_publish:
			if g_blog.sitemap_ping:
				Sitemap_NotifySearch()

		if old_publish and not is_publish:
			self.update_archive(-1)
		if not old_publish and is_publish:
			self.update_archive(1)

		self.removecache()

		self.put()
		g_blog.tigger_action("save_post",self,is_publish)




	def removecache(self):
		memcache.delete('/')
		memcache.delete('/'+self.link)
		memcache.delete('/sitemap')
		memcache.delete('blog.postcount')
		g_blog.tigger_action("clean_post_cache",self)

	@property
	def next(self):
		return Entry.all().filter('entrytype = ',self.entrytype).filter("published =", True).order('post_id').filter('post_id >',self.post_id).fetch(1)


	@property
	def prev(self):
		return Entry.all().filter('entrytype = ',self.entrytype).filter("published =", True).order('-post_id').filter('post_id <',self.post_id).fetch(1)

	@property
	def relateposts(self):
		if  self._relatepost:
			return self._relatepost
		else:
			if self.tags:
				self._relatepost= Entry.gql("WHERE published=True and tags IN :1 and post_id!=:2 order by post_id desc "\
				,self.tags,self.post_id).fetch(5)
			else:
				self._relatepost= []
			return self._relatepost

	@property
	def trackbackurl(self):
		if self.link.find("?")>-1:
			return g_blog.tigger_adminurl('trackbackurlo',g_blog.baseurl,self.link,str(self.key()))
		else:
			return g_blog.tigger_adminurl('trackbackurlt',g_blog.baseurl,self.link,str(self.key()))

	def getbylink(self):
		pass

	def Delete(self):
		g_blog.tigger_action("pre_delete_post",self)
		if self.published:
			self.update_archive(-1)
		self.delete_comments()
		db.Model.delete(self)
		g_blog.tigger_action("delete_post",self)
		return True

	def Images(self):
			try:
					img=re.compile(r"""<img\s.*?\s?src\s*=\s*['|"]?([^\s'"]+).*?>""",re.I)
					m = img.findall(self.content)
					return m
			except Exception,data:
					logging.info('the error is %s',data)
					return '/static/images/cover.jpg'

	def Simages(self):
			try:
					img=re.compile(r"""<img\s.*?\s?src\s*=\s*['|"]?([^\s'"]+).*?>""",re.I)
					m = img.findall(self.content)
					n=re.findall(r"""[^?'"]+.*?""",m[0])[1]
					return self.PhotoUrl_s(n)



			except Exception,data:
					logging.info('the error is %s',data)
					return '/static/images/cover.jpg'

	def Imageentry(self):
			return Entry.all().filter('imageurl != ',None)

	def Fetchcats(self,slug):
			cats=Category.all().filter('slug = ',slug).fetch(1)
			if cats==None:
					return None
			else:

					return cats[0].key()



class User(db.Model):
	user = db.UserProperty(required = False)
	dispname = db.StringProperty()
	email=db.StringProperty()
	website = db.LinkProperty()
	isadmin=db.BooleanProperty(default=False)
	isAuthor=db.BooleanProperty(default=True)
	#rpcpwd=db.StringProperty()

	def __unicode__(self):
		#if self.dispname:
			return self.dispname
		#else:
		#	return self.user.nickname()

	def __str__(self):
		return self.__unicode__().encode('utf-8')

COMMENT_NORMAL=0
COMMENT_TRACKBACK=1
COMMENT_PINGBACK=2
class Comment(db.Model):
	entry = db.ReferenceProperty(Entry)
	date = db.DateTimeProperty(auto_now_add=True)
	content = db.TextProperty(required=True)
	author=db.StringProperty()
	email=db.EmailProperty()
	weburl=db.URLProperty()
	status=db.IntegerProperty(default=0)
	reply_notify_mail=db.BooleanProperty(default=False)
	ip=db.StringProperty()
	ctype=db.IntegerProperty(default=COMMENT_NORMAL)
	comment_order=db.IntegerProperty(default=1)


	@classmethod
	@vcache(time=360000)
	def Get_comment(self,mode='all'):
			if mode=='all':
				return Comment.all().order('-date').fetch(5)
			else:
				return Comment.all().filter('media = ',mode).order('-date').fetch(5)

	@property
	def shortcontent(self,len=20):
		scontent=self.content
		scontent=re.sub(r'<br\s*/>',' ',scontent)
		scontent=re.sub(r'<[^>]+>','',scontent)
		scontent=re.sub(r'(@[\S]+)-\d+[:]',r'\1:',scontent)
		return scontent[:len].replace('<','&lt;').replace('>','&gt;')


	def gravatar_url(self):

		# Set your variables here
		default = g_blog.baseurl+'/static/images/homsar.jpeg'
		if not self.email:
			return default

		size = 50

		try:
			# construct the url
			imgurl = "http://www.gravatar.com/avatar/"
			imgurl +=hashlib.md5(self.email).hexdigest()+"?"+ urllib.urlencode({
				'd':default, 's':str(size),'r':'G'})
			return imgurl
		except:
			return default

	def save(self):


		self.put()
		self.entry.commentcount+=1
		self.comment_order=self.entry.commentcount
		self.entry.put()
		memcache.delete("/"+self.entry.link)




	def delit(self):
		self.entry.commentcount-=1
		self.entry.put()
		self.delete()

	def put(self):
		g_blog.tigger_action("pre_comment",self)
		db.Model.put(self)
		g_blog.tigger_action("save_comment",self)

	def delete(self):
		db.Model.delete(self)
		g_blog.tigger_action("delete_comment",self)

	@property
	def children(self):
		key=self.key()
		comments=Comment.all().ancestor(self)
		return [c for c in comments if c.parent_key()==key]



class Albums(db.Model):
	#TODO 相册数据模型
	albumname = db.StringProperty()
	photocount = db.IntegerProperty(default=0)
	albumpassword = db.StringProperty()
	albumcreatedate = db.DateTimeProperty(auto_now_add = True)
	albumauthor = db.UserProperty()
	lastupdate = db.DateTimeProperty(auto_now=True)
	createdate = db.DateTimeProperty(auto_now_add = True)
	displayorder = db.IntegerProperty(default = 0)
	coverid = db.StringProperty()
	public =db.BooleanProperty(default=True)
	post_id= db.IntegerProperty()
	link= db.StringProperty(multiline=False,default='')
	tag=db.ReferenceProperty(Tag,collection_name='a_tag')

	def Getalbum(self,id):
		return self.get_by_id(id)
	def id(self):
	    return str(self.key().id())
	def Save(self):
	    self.put()
	def Delete(self):
	    for a in self.Photos():
			a.Delete()
			self.Delete()

	def Cover(self):
#TODO the small cover of albums,this the key of photo,the 'm' is the image size
			if len(self.coverid) > 0:
					return g_blog.tigger_adminurl('albumcover',os.environ['HTTP_HOST'],self.coverid)
			else:
					return '/static/images/cover.jpg'

	def Coverbigg(self):
#TODO the big cover of albums,this the key of photo
			if len(self.coverid) > 0:
					return g_blog.tigger_adminurl('albumcoverb',os.environ['HTTP_HOST'],self.coverid)
			else:
					return '/static/images/cover.jpg'

	def Coveradmin(self):
#TODO the admin system cover of albums,this the key of photo,the 'm' is the image size
		try:
			if self.coverid!=None :
					return g_blog.tigger_adminurl('albumcovera',os.environ['HTTP_HOST'],self.coverid)
			else:
					return '/static/images/cover.jpg'
		except Exception,data:
			logging.info(data)



	def Tag(self):
		return self.tag.tag

	def Tag_url(self):
		return self.tag.Tagurl

	def AlbumUrl(self):
		return g_blog.tigger_adminurl('albumurl',os.environ['HTTP_HOST'],self.key().id())

	@vcache(first='album_GetAll',time=360000)
	def GetAll(self):
	    return Albums.all().order('displayorder').order('-lastupdate').fetch(1000)


	def Photos(self):
	    photos =  Media.all().filter('Album =',self).order('-date').fetch(100)
	    return photos

	@vcache(first='GetlatestPhoto',time=360000)
	def GetlatestPhoto(self,v):
		"""
		this methods is used for get the latest photos
		"""
		try:
			if type(v)!='int':
				v=10
			photos=Media().all().filter('public = ',True).filter('Album != ','null').order('-Album').order('-date').fetch(v)

			return photos
		except:
			return None


	def Gettopviews(self,v):
		if type(v)!='int':
			v=10
		photos=Media().all().filter('public = ',True).filter('Album != ',None).order('-Album').order('-viewcount').fetch(v)


		return photos


	def Gettopcomment(self,v):
		if type(v)!='int':
			v=10
		photos=Media().all().filter('public = ',True).filter('Album != ',None).order('-Album').order('-commentcount').fetch(v)


		return photos

	def Link_url(self):
		return g_blog.tigger_adminurl('albumlink',g_blog.albumurl,self.id())

	@property
	def Edit_url(self):
		return g_blog.tigger_adminurl('albumeditlink',self.id())

	def settags(self,values):
		if values:
			tags=Tag.all()
			for v in tags:
					if v.tag== values:
						return v
					else:
						return Tag.add(values,'album')
						break
		else:
			return None

	def GetAlbumBytag(self,tagname):
		"""
		if we can not find the tag,we return the None
		if we can find the tag,we return the albums which belong the tag
		"""
		tagkey=''
		for tag in Tag.all():
						if tag.tag == tagname:
								tagkey=tag.key()
		if tagkey:
				albums=Albums.all().filter("public =", True).filter('tag =',tagkey).order("-createdate")
				return albums
		else:
				return None


	def Gallery_url(self):
		return g_blog.tigger_adminurl('gallerylink',self.key())


class Media(db.Model):
	name =db.StringProperty()
	filename=db.StringProperty()
	mtype=db.StringProperty()
	size=db.IntegerProperty(default=0)
	date=db.DateTimeProperty(auto_now_add=True)
	download=db.IntegerProperty(default=0)
	filekey=blobstore.BlobReferenceProperty()
	user = db.UserProperty()
	description = db.TextProperty(default=u'请输入说明介绍文字')
	viewcount = db.IntegerProperty(default = 0)
	width = db.IntegerProperty()
	height = db.IntegerProperty()
	EXIF = db.StringProperty()
	state = db.IntegerProperty(default = 1)
	Album = db.ReferenceProperty(Albums)
	commentcount = db.IntegerProperty(default=0)
	public = db.BooleanProperty(default=True)
	categories =db.ReferenceProperty(Category)
	tag =db.ReferenceProperty(Tag,'m_tag')
	post_id= db.IntegerProperty()
	link= db.StringProperty(multiline=False,default='')
	url= db.StringProperty(default='http://ccdm.tk')
	allow_comment=db.BooleanProperty(default=True)
	oldurl=db.StringProperty()
	blobfile=db.BlobProperty()

	def Delete(self):
		if g_blog.blobstore:
				self.filekey.delete()
		if self.Album:
				self.Album.photocount-=1
		self.delete()
		g_blog.mediacount-=1
		g_blog.save()
		return True
	def id(self):
		return str(self.key().id())

	def Save(self):
		#TODO 添加或修改____
		g_blog.mediacount+=1
		g_blog.save()

		self.put()
		self.Album.photocount +=1


		self.Album.Save()

	def PhotoUrl(self):
		return g_blog.tigger_adminurl('photolink',os.environ['HTTP_HOST'],self.key())

	def PhotoUrl_s(self):
		return g_blog.tigger_adminurl('photolinks',os.environ['HTTP_HOST'],self.key())

	def PhotoUrl_c(self):
		return g_blog.tigger_adminurl('photolinkc',os.environ['HTTP_HOST'],self.key())

	def PhotoUrl_g(self):
		return g_blog.tigger_adminurl('photolinkg',os.environ['HTTP_HOST'],self.key())

	def Update(self):
	    self.put()

	def Prev(self):
	    prev =  Media.all().filter('Album',self.Album).filter('date < ',self.date).order('-date').fetch(1)
	    if len(prev) == 1:
	        return prev[0]
	    return None

	def Next(self):
			next =  Media.all().filter('Album',self.Album).filter('date > ',self.date).order('date').fetch(1)
			if len(next) == 1:
				return next[0]
			return None

	@vcache(first='Recentcomm',time=360000)
	def Recentcomm(self):
		return Acomment.all().order('-date').fetch(10)


	def Images(self):
			try:
					img=re.compile(r"""<img\s.*?\s?src\s*=\s*['|"]?([^\s'"]+).*?>""",re.I)
					m = img.findall(self.content)
					return m
			except Exception,data:
					logging.info('the error is %s',data)
					return '/static/images/cover.jpg'

	@property
	def Link_url(self):
		try:
			if len(self.link)>0:
				return g_blog.tigger_adminurl('photolinkurlo',g_blog.baseurl,self.link)
			else:
				return g_blog.tigger_adminurl('photolinkurlt',g_blog.baseurl,str(self.key()))
		except Exception,data:
			logging.info(data)

	@property
	def Edit_url(self):
			return g_blog.tigger_adminurl('photolinkedit',self.key(),self.Album.id())

	def get_comments_by_page(self,index,psize):
			return self.media_photo.fetch(psize,offset = (index-1) * psize)


class Acomment(Comment):
	photo=db.ReferenceProperty(Media,collection_name='media_photo')

	def save(self):


		self.put()
		self.photo.commentcount+=1
		self.comment_order=self.photo.commentcount
		self.photo.put()
		memcache.delete("/"+str(self.photo.key()))

class OtherDoc(db.Model):
	name=db.StringProperty()
	value=db.TextProperty()
	date=db.DateTimeProperty(auto_now_add=True)


	def Getdoc(self,docname):
		if docname!=None:
				result=self.all().filter('name =',docname).fetch(1)
				if result:
						return result[0]
				else:
						return u'Page is under construction'
		else:
				return None

class WikiSettings(db.Model):
  title = db.StringProperty()
  start_page = db.StringProperty()
  admin_email = db.StringProperty()
  # publicly readable
  pread = db.BooleanProperty(True)
  # publicly writable
  pwrite = db.BooleanProperty(False)
  # Google Site Ownership Verification,
  # http://www.google.com/support/webmasters/bin/answer.py?answer=35659
  owner_meta = db.StringProperty()
  # page footer
  footer = db.TextProperty()
  interwiki = db.TextProperty()

class WikiUser(db.Model):
  wiki_user = db.UserProperty()
  joined = db.DateTimeProperty(auto_now_add=True)
  wiki_user_picture = db.BlobProperty()
  user_feed = db.StringProperty()

class WikiContent(db.Model):
  title = db.StringProperty(required=True)
  body = db.TextProperty(required=False)
  author = db.ReferenceProperty(WikiUser)
  updated = db.DateTimeProperty(auto_now_add=True)
  pread = db.BooleanProperty()

class WikiRevision(db.Model):
  wiki_page = db.ReferenceProperty(WikiContent)
  revision_body = db.TextProperty(required=True)
  author = db.ReferenceProperty(WikiUser)
  created = db.DateTimeProperty(auto_now_add=True)
  version_number = db.IntegerProperty()
  pread = db.BooleanProperty()

class OptionSet(db.Model):
	name=db.StringProperty()
	value=db.TextProperty()
	#blobValue=db.BlobProperty()
	#isBlob=db.BooleanProperty()

	@classmethod
	def getValue(cls,name,default=None):
		try:
			opt=OptionSet.get_by_key_name(name)
			return pickle.loads(str(opt.value))
		except:
			return default

	@classmethod
	def setValue(cls,name,value):
		opt=OptionSet.get_or_insert(name)
		opt.name=name
		opt.value=pickle.dumps(value)
		opt.put()

	@classmethod
	def remove(cls,name):
		opt= OptionSet.get_by_key_name(name)
		if opt:
			opt.delete()

NOTIFICATION_SITES = [
  ('http', 'www.google.com', 'webmasters/sitemaps/ping', {}, '', 'sitemap')
  ]


def Sitemap_NotifySearch():
	""" Send notification of the new Sitemap(s) to the search engines. """


	url=g_blog.baseurl+"/sitemap"

	# Cycle through notifications
	# To understand this, see the comment near the NOTIFICATION_SITES comment
	for ping in NOTIFICATION_SITES:
	  query_map			 = ping[3]
	  query_attr			= ping[5]
	  query_map[query_attr] = url
	  query = urllib.urlencode(query_map)
	  notify = urlparse.urlunsplit((ping[0], ping[1], ping[2], query, ping[4]))
	  try:
		urlfetch.fetch(notify)

	  except :
		logging.error('Cannot contact: %s' % ping[1])

def InitBlogData():
	global g_blog
	OptionSet.setValue('PluginActive',[u'googleAnalytics', u'wordpress', u'sys_plugin'])
#TODO:the blog url is here
	g_blog = Blog(key_name = 'default')
	g_blog.domain=os.environ['HTTP_HOST']
	g_blog.baseurl="http://"+g_blog.domain
	g_blog.feedurl=g_blog.baseurl+"/feed"
	g_blog.blogurl=g_blog.baseurl+"/blog"
	g_blog.albumurl=g_blog.baseurl+"/album"
	g_blog.downloadurl=g_blog.baseurl+"/download"
	g_blog.articleurl=g_blog.baseurl+"/article"
	os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
	lang="zh-cn"
	if os.environ.has_key('HTTP_ACCEPT_LANGUAGE'):
		lang=os.environ['HTTP_ACCEPT_LANGUAGE'].split(',')[0]
	from django.utils.translation import  activate,to_locale
	g_blog.language=to_locale(lang)
	from django.conf import settings
	settings._target = None
	activate(g_blog.language)
	g_blog.save()

	entry=Entry(title=_("Hello world!").decode('utf8'))
	entry.content=_('<p>Welcome to CDM SYSTEM. This is your first post. Edit or delete it, then start the CDM!</p>').decode('utf8')
	entry.entrytype='blog'
	entry.save(True)
	link=Link(href='http://ccdm.tk',linktext=_("ChinaCDM's website").decode('utf8'))
	link.put()
	return g_blog

def gblog_init():
	global g_blog
	try:
	   if g_blog :
		   return g_blog
	except:
		pass
	g_blog = Blog.get_by_key_name('default')
	if not g_blog:
		g_blog=InitBlogData()


	g_blog.get_theme()
	g_blog.rootdir=os.path.dirname(__file__)
	return g_blog

try:
	g_blog=gblog_init()

	os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
	from django.utils.translation import  activate
	from django.conf import settings
	settings._target = None
	activate(g_blog.language)
except:
	pass
