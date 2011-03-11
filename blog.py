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
import cgi, os,sys,math
import wsgiref.handlers
import  google.appengine.api

# Google App Engine imports.
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template,WSGIApplication
from google.appengine.api import users
from google.appengine.ext import db
from datetime import datetime ,timedelta
import base64,random
from django.utils import simplejson
import filter  as myfilter
from django.template.loader import *
from app.safecode import Image
from app.gmemsess import Session
from base import *
from model import *
import logging
from google.appengine.ext import zipserve
from google.appengine.api import memcache

def doRequestHandle(old_handler,new_handler,**args):
	"""
	TODO:The Helper method to request handler
	"""
	new_handler.initialize(old_handler.request,old_handler.response)
	return  new_handler.get(**args)

def doRequestPostHandle(old_handler,new_handler,**args):
	"""
	TODO:The Helper method to request.post handler
	"""
	new_handler.initialize(old_handler.request,old_handler.response)
	return  new_handler.post(**args)

"""
TODO:the base calss of blog package
"""
class BasePublicPage(BaseRequestHandler):
		"""
		TODO: Initialize of BasePublicPage class.

		"""
		def initialize(self, request, response):
				BaseRequestHandler.initialize(self,request, response)
				skey=request.path_qs
				#logging.info(skey)
				html= memcache.get(skey)
				if not html:
						m_pages=Entry.Get_mpages()
						blogroll=Link.Get_blogroll()
						archives=Archive.Get_archive()
						alltags=Tag.Get_tag()

						self.template_vals.update({
								'menu_pages':m_pages,
								'categories':Category.Get_category('blog'),
								'dcategories':Category.Get_category('download'),
								'acategories':Category.Get_category('article'),
								'allcategories':Category.Get_category('all'),
								'blogroll':blogroll,
								'archives':archives,
								'alltags':alltags,
								'recent_comments':Comment.Get_comment('all'),
								'recent_bcomments':Comment.Get_comment('blog'),
								'recent_dcomments':Comment.Get_comment('download'),
								'recent_acomments':Comment.Get_comment('article')
						})

		@vcache(key='m_list_pages')
		def m_list_pages(self):

				menu_pages=None
				entry=None
				if self.template_vals.has_key('menu_pages'):
					menu_pages= self.template_vals['menu_pages']
				if self.template_vals.has_key('entry'):
					entry=self.template_vals['entry']
				ret=''
				current=''
				for page in menu_pages:
					if entry and entry.entrytype=='page' and entry.key()==page.key():
						current= 'current_page_item'
					else:
						current= 'page_item'
					"""
					page is external page ,and page.slug is none.
					"""
					if page.is_external_page and not page.slug:
						ret+='<li class="%s"><a href="%s" target="%s" >%s</a></li>'%( current,page.link,page.target, page.title)
					else:
						ret+='<li class="%s"><a href="/%s" target="%s">%s</a></li>'%( current,page.link, page.target,page.title)
				return ret
		@vcache(first='sticky_entrys')
		def sticky_entrys(self,mode='post',n='100'):
				"""
				this is used to show the sticky post.
				mode=the post type,like article\blog\download\page
				n=the number of you want to show
				"""
				return Entry.all().filter('entrytype =',mode)\
						.filter('published =',True)\
						.filter('sticky =',True)\
						.order('-date').fetch(n)
		@vcache(first='hot_entrys')
		def hot_entrys(self,mode='post',n='100'):
				"""
				this is used to show the hot post.
				mode=the post type,like article\blog\download\page
				n=the number of you want to show
				"""
				if mode=='all':
					return Entry.all().filter('published =',True)\
						.order('-readtimes').fetch(n)
				else:
					return Entry.all().filter('entrytype =',mode)\
						.filter('published =',True)\
						.order('-readtimes').fetch(n)
		@vcache(first='show_latest')
		def show_latest(self,mode='post',n='100'):
				"""
				this is used to show the new post.
				mode=the post type,like article\blog\download\page
				n=the number of you want to show
				"""
				return Entry.all().filter('entrytype =',mode)\
						.filter('published =',True)\
						.order('-date').fetch(n)

		def Checkmode(self):
				mode=self.request.path_info
				if '/blog' in mode:
						mode='blog'
				elif '/download' in mode:
						mode='download'
				elif '/article' in mode:
						mode='article'
				elif mode.split('/')[1]=='page':
						mode='page'
				else:
						if g_blog.blogtype=='cms':
								mode='index'
						else:
								mode='blog'
				return mode

		def Checkperpage(self,mode):
				if mode == 'blog':
						return g_blog.posts_per_page
				elif mode == 'article':
						return g_blog.article_per_page
				elif mode == 'download':
						return g_blog.media_per_page
				else:
						return g_blog.posts_per_page

class MainPage(BasePublicPage):

		@cache(mime='text/html')
		def get(self,page=1):
				postid=self.param('p')
				if postid:
						try:
								postid=int(postid)
								return doRequestHandle(self,SinglePost(),postid=postid)  #singlepost.get(postid=postid)
						except:
								return self.error(404)
				#check the blog type

				Web_mode=self.Changmode(page)
		def post(self):
				postid=self.param('p')
				if postid:
						try:
								postid=int(postid)
								return doRequestPostHandle(self,SinglePost(),postid=postid)  #singlepost.get(postid=postid)
						except:
								return self.error(404)



		def doget(self,page,mode):
				page=int(page)
				entries = Entry.all().filter('entrytype =',mode).\
					filter("published =", True).order('-date')
				items_per_page=self.Checkperpage(mode)
				thetop=self.sticky_entrys(mode,n=5)
				show_hot=self.hot_entrys(mode,n=20)
				show_latest=self.show_latest(mode,n=10)
				if mode=='blog':
					index=True
				else:
					index=False
				entries,links=Pager(query=entries,items_per_page=items_per_page).fetch(page,self.request.path_info,index)
				return self.render(mode,{'entries':entries,
						'pager' : links,
						'thetop':thetop,
						'show_hot':show_hot,
						'show_latest':show_latest,
						'pageindex':page,
						'ishome':True
						})


		def dogetcms(self,page,mode='page'):
				#try:
						cms=CmsPublicPage().get_mode(mode)
						return self.render(mode,{'cms':cms})
				#except Exception,data:
				#		logging.info(data)

		def Changmode(self,page):
				mode=self.Checkmode()
				if mode == 'blog':
						self.doget(page,mode)
				else:
						if g_blog.blogtype=='cms':
								self.dogetcms(page,mode)
						else:
								#mode='blog'
								self.doget(page,mode)

		def Typecount(self,mode):
				if mode == 'blog':
						return g_blog.postscount()
				elif mode == 'download':
						return g_blog.downloadscount()
				elif mode == 'article':
						return g_blog.articlescount()

class CmsPublicPage(MainPage):
		_mode=''
		def get_mode(self,mode):
				self._mode=mode
				return self
		def Entry(self):
				return Entry().all().filter('entrytype = ',self._mode)
		def Sticky(self):
				return Entry().all().filter('entrytype = ',self._mode).filter('sticky = ',True)
		def Imageentry(self):
				return Entry().all().filter('entrytype = ',self._mode).filter('imageurl != ',None)

		def Pageentry(self):
				return Entry().all().filter('entrytype = ','page')
		def Show_hot(self):
				return Entry().all().filter('entrytype = ',self._mode).order('-readtimes')

		def Indexentry(self):
				return Entry().all()

class entriesByCategory(BasePublicPage):
		@cache(mime='text/html')
		def get(self,slug=None):
				if not slug:

						self.error(404)
						return
				try:

						page_index=self.Getpage()
				except:
						page_index=1
				slug=self.Getslug(slug)
				cats=Category.all().filter('slug =',slug).fetch(1)
				if cats:
						mode=self.Checkmode()
						items_per_page=self.Checkperpage(mode)
						entries=Entry.all().filter("published =", True).filter('categorie_keys =',cats[0].key()).order("-date")
						entries,links=Pager(query=entries,items_per_page=items_per_page).fetch(page_index,self.request.path_info)
						thetop=self.sticky_entrys(mode,10)
						show_hot=self.hot_entrys(mode,10)
						self.render(mode+'category',{'entries':entries,'category':cats[0],'pager':links,'thetop':thetop,'show_hot':show_hot})
				else:
						self.error(414,slug)


class archive_by_month(BasePublicPage):
	@cache(mime='text/html')
	def get(self,year,month,*arg):

		try:
			page_index=self.Getpage()
		except:
			page_index=1

		firstday=datetime(int(year),int(month),1)
		if int(month)!=12:
			lastday=datetime(int(year),int(month)+1,1)
		else:
			lastday=datetime(int(year)+1,1,1)
		entries=db.GqlQuery("SELECT * FROM Entry WHERE date > :1 AND date <:2 AND entrytype in :3\
		AND published = True ORDER BY date DESC",firstday,lastday,['blog','download','photo','article'])
		mode='%s/%s'% (year,month)
		entries,links=Pager(query=entries).fetch(page_index,self.request.path_info)

		self.render('month',{'entries':entries,'year':year,'month':month,'pager':links})

class entriesByTag(BasePublicPage):
		@cache(mime='text/html')
		def get(self,slug=None):
				if not slug:
						self.error(404)
						return
				try:
						page_index=int (self.param('page'))
				except:
						page_index=1
				import urllib
				slug=urldecode(slug)

				entries=Entry.all().filter("published =", True).filter('tags =',slug).order("-date")
				entries,links=Pager(query=entries,items_per_page=20).fetch(page_index)
				show_hot=self.hot_entrys('all',9)
				self.render('tag',{'entries':entries,'tag':slug,'pager':links,'show_hot':show_hot})




class SinglePost(BasePublicPage):
		@cache(mime='text/html')
		def get(self,slug=None,postid=None):
				"""
				singlepost is the class for single page
				Postid and p is the key of request.GET,so we check them

				"""
				if postid:
						entries = Entry.all().filter("published =", True).filter('post_id =', postid).fetch(1)
				elif self.param('p'):
						entries = Entry.all().filter("published =", True).filter('post_id =', int(self.param('p'))).fetch(1)
				else:
						slug=urldecode(slug)
						if slug[:1] !='/':
								if slug.find('/')!=-1:
									slug=g_blog.tigger_adminurl('entrylink',self.Checkmode(),slug)
								else:
									slug='/page/%s'% slug
						entries = Entry.all().filter("published =", True).filter('link =', slug).fetch(1)
				if not entries or len(entries) == 0:
						return self.error(404)

				mp=self.paramint("mp",1)
				entry=entries[0]
				if entry.is_external_page:
				    return self.redirect(entry.external_page_address,True)
				if g_blog.allow_pingback and entry.allow_trackback:
				    self.response.headers['X-Pingback']="%s/rpc"%str(g_blog.baseurl)
				entry.readtimes += 1
				entry.put()
				self.entry=entry


				comments=entry.get_comments_by_page(mp,self.blog.comments_per_page)


			##      commentuser=self.request.cookies.get('comment_user', '')
			##      if commentuser:
			##          commentuser=commentuser.split('#@#')
			##      else:
				commentuser=['','','']

				comments_nav=self.get_comments_nav(mp,entry.comments().count())
				thetop=self.sticky_entrys(entry.entrytype,n=5)
				show_hot=self.hot_entrys(entry.entrytype,n=20)
				show_latest=self.show_latest(entry.entrytype,n=10)
				if entry.entrytype=='post' or entry.entrytype=='blog':
						self.render('single',
						{
						'entry':entry,
						'relateposts':entry.relateposts,
						'comments':comments,
						'user_name':commentuser[0],
						'user_email':commentuser[1],
						'user_url':commentuser[2],
						'show_hot':show_hot,
						'thetop':thetop,
						'show_latest':show_latest,
						'checknum1':random.randint(1,10),
						'checknum2':random.randint(1,10),
						'comments_nav':comments_nav,
						})

				elif entry.entrytype=='page':
						self.render('page',
						{'entry':entry,
						'relateposts':entry.relateposts,
						'comments':comments,
						'user_name':commentuser[0],
						'user_email':commentuser[1],
						'user_url':commentuser[2],
						'show_hot':show_hot,
						'thetop':thetop,
						'show_latest':show_latest,
						'checknum1':random.randint(1,10),
						'checknum2':random.randint(1,10),
						'comments_nav':comments_nav,
						})
				elif entry.entrytype=='download':
						self.render('dsingle',
								{'entry':entry,
								'relateposts':entry.relateposts,
								'comments':comments,
								'user_name':commentuser[0],
								'user_email':commentuser[1],
								'user_url':commentuser[2],
								'show_hot':show_hot,
								'thetop':thetop,
								'show_latest':show_latest,
								'checknum1':random.randint(1,10),
								'checknum2':random.randint(1,10),
								'comments_nav':comments_nav,
								})
				elif entry.entrytype=='article':
						self.render('asingle',
								{'entry':entry,
								'relateposts':entry.relateposts,
								'comments':comments,
								'user_name':commentuser[0],
								'user_email':commentuser[1],
								'user_url':commentuser[2],
								'show_hot':show_hot,
								'thetop':thetop,
								'show_latest':show_latest,
								'checknum1':random.randint(1,10),
								'checknum2':random.randint(1,10),
								'comments_nav':comments_nav,
								})

		def post(self,slug=None,postid=None):
				'''handle trackback'''
				error = '''
			<?xml version="1.0" encoding="utf-8"?>
			<response>
			<error>1</error>
			<message>%s</message>
			</response>
			'''
				success = '''
			<?xml version="1.0" encoding="utf-8"?>
			<response>
			<error>0</error>
			</response>
			'''

				if not g_blog.allow_trackback:
				    self.response.out.write(self.error % "Trackback denied.")
				    return
				self.response.headers['Content-Type'] = "text/xml"
				if postid:
				    entries = Entry.all().filter("published =", True).filter('post_id =', postid).fetch(1)
				else:
				    slug=urldecode(slug)
				    entries = Entry.all().filter("published =", True).filter('link =', slug).fetch(1)

				if not entries or len(entries) == 0 :#or  (postid and not entries[0].link.endswith(g_blog.default_link_format%{'post_id':postid})):
				    self.response.out.write(error % "empty slug/postid")
				    return
				#check code ,rejest spam
				entry=entries[0]
				#key=self.param("code")
				#if (self.request.uri!=entry.trackbackurl) or entry.is_external_page or not entry.allow_trackback:
				import cgi
				param=cgi.parse_qs(self.request.uri)
				if param.has_key('code'):
				    code=param['code'][0]

				if  (not str(entry.key())==code) or entry.is_external_page or not entry.allow_trackback:
				    self.response.out.write(error % "Invalid trackback url.")
				    return


				coming_url = self.param('url')
				blog_name = myfilter.do_filter(self.param('blog_name'))
				excerpt = myfilter.do_filter(self.param('excerpt'))
				title = myfilter.do_filter(self.param('title'))

				if not coming_url or not blog_name or not excerpt or not title:
				    self.response.out.write(error % "not enough post info")
				    return

				import time
				#wait for half second in case otherside hasn't been published
				time.sleep(0.5)

			##      #also checking the coming url is valid and contains our link
			##      #this is not standard trackback behavior
			##      try:
			##
			##          result = urlfetch.fetch(coming_url)
			##          if result.status_code != 200 :
			##              #or ((g_blog.baseurl + '/' + slug) not in result.content.decode('ascii','ignore')):
			##              self.response.out.write(error % "probably spam")
			##              return
			##      except Exception, e:
			##          logging.info("urlfetch error")
			##          self.response.out.write(error % "urlfetch error")
			##          return

				comment = Comment.all().filter("entry =", entry).filter("weburl =", coming_url).get()
				if comment:
				    self.response.out.write(error % "has pinged before")
				    return

				comment=Comment(author=blog_name,
					content="<strong>"+title[:250]+"...</strong><br/>" +
						excerpt[:250] + '...',
					weburl=coming_url,
					entry=entry)

				comment.ip=self.request.remote_addr
				comment.ctype=COMMENT_TRACKBACK
				try:
				    comment.save()

				    memcache.delete("/"+entry.link)
				    self.write(success)
				    g_blog.tigger_action("pingback_post",comment)
				except:
				    self.response.out.write(error % "unknow error")

		def get_comments_nav(self,pindex,count):

				maxpage=count / g_blog.comments_per_page + ( count % g_blog.comments_per_page and 1 or 0 )
				if maxpage==1:
				    return ""

				result=""

				if pindex>1:
				    result="<a class='comment_prev' href='"+self.get_comments_pagenum_link(pindex-1)+"'>«</a>"

				minr=max(pindex-3,1)
				maxr=min(pindex+3,maxpage)
				if minr>2:
				    result+="<a class='comment_num' href='"+self.get_comments_pagenum_link(1)+"'>1</a>"
				    result+="<span class='comment_dot' >...</span>"

				for  n in range(minr,maxr+1):
				    if n==pindex:
					result+="<span class='comment_current'>"+str(n)+"</span>"
				    else:
					result+="<a class='comment_num' href='"+self.get_comments_pagenum_link(n)+"'>"+str(n)+"</a>"
				if maxr<maxpage-1:
				    result+="<span class='comment_dot' >...</span>"
				    result+="<a class='comment_num' href='"+self.get_comments_pagenum_link(maxpage)+"'>"+str(maxpage)+"</a>"

				if pindex<maxpage:
				    result+="<a class='comment_next' href='"+self.get_comments_pagenum_link(pindex+1)+"'>»</a>"

				return {'nav':result,'current':pindex,'maxpage':maxpage}

		def get_comments_pagenum_link(self,pindex):
				url=str(self.entry.link)
				if url.find('?')>=0:
						return g_blog.tigger_adminurl('entrycommurlo',url,str(pindex))
				else:
						return g_blog.tigger_adminurl('entrycommurlt',url,str(pindex))

class FeedHandler(BaseRequestHandler):
    @cache(time=72000,mime='text/xml')
    def get(self,tags=None):
        entries = Entry.all().filter('entrytype in',['post','article','blog','download']).filter('published =',True).order('-date').fetch(20)
        if entries and entries[0]:
            last_updated = entries[0].date
            last_updated = last_updated.strftime("%Y-%m-%dT%H:%M:%SZ")
        for e in entries:
            e.formatted_date = e.date.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.response.headers['Content-Type'] = 'application/atom+xml'
        self.render2('views/atom.xml',{'entries':entries,'last_updated':last_updated})

class CommentsFeedHandler(BaseRequestHandler):
    @cache(time=72000,mime='text/xml')
    def get(self,tags=None):
	last_updated=''
        comments = Comment.all().order('-date').fetch(10)
        if comments and comments[0]:
            last_updated = comments[0].date
            last_updated = last_updated.strftime("%Y-%m-%dT%H:%M:%SZ")
        for e in comments:
            e.formatted_date = e.date.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.response.headers['Content-Type'] = 'application/atom+xml'
        self.render2('views/comments.xml',{'comments':comments,'last_updated':last_updated})

class SitemapHandler(BaseRequestHandler):
    @cache(time=36000,mime='text/xml')
    def get(self,tags=None):
        urls = []
        def addurl(loc,lastmod=None,changefreq=None,priority=None):
            url_info = {
                'location':   loc,
                'lastmod':  lastmod,
                'changefreq': changefreq,
                'priority':   priority
            }
            urls.append(url_info)

        addurl(g_blog.baseurl,changefreq='daily',priority=0.9 )

        entries = Entry.all().filter('published =',True).order('-date').fetch(g_blog.sitemap_entries)

        for item in entries:
            loc = "%s/%s" % (g_blog.baseurl, item.link)
            addurl(loc,item.mod_date or item.date,'never',0.6)

        if g_blog.sitemap_include_category:
            cats=Category.all()
            for cat in cats:
		loc=g_blog.baseurl+g_blog.tigger_adminurl('category',cat.media,cat.slug)
		addurl(loc,None,'weekly',0.5)

        if g_blog.sitemap_include_tag:
            tags=Tag.all()
            for tag in tags:
		loc=g_blog.baseurl+g_blog.tigger_adminurl('tag',urlencode(tag.tag))
		addurl(loc,None,'weekly',0.5)


##      self.response.headers['Content-Type'] = 'application/atom+xml'
        self.render2('views/sitemap.xml',{'urlset':urls})


class Error404(BaseRequestHandler):
    @cache(time=360000,mime='text/html')
    def get(self,slug=None):
        self.error(404)

class Update_cate_count(BaseRequestHandler):
	def get(self,slug=None):
		caties=Category.all()
		entrycount=0
		for cate in caties:
				cate.Update_count()
				entrycount+=cate.post_count
		#entrycount=len(list(Entry.all().filter('entrytype = ','blog').filter("published =", True).order('-date')))
		mediacount=len(list(Media.all().order('-date')))
		albumcount=len(list(Albums.all().filter('public = ',True).order('-createdate')))
		g_blog.entrycount=entrycount
		g_blog.mediacount=mediacount
		g_blog.albumcount=albumcount
		g_blog.put()

class Post_comment(BaseRequestHandler):
	#@printinfo
	"""
	TODO:this one is used for comments
	"""
	def post(self,slug=None):
		useajax=self.param('useajax')=='1'

		name=self.param('author')
		email=self.param('email')
		url=self.param('url')

		key=self.param('key')
		content=self.param('comment')
		parent_id=self.paramint('parentid',0)
		reply_notify_mail=self.parambool('reply_notify_mail')


		sess=Session(self,timeout=180)
		if not self.is_login:
			try:
				check_ret=True
				if g_blog.comment_check_type in (1,2)  :
					checkret=self.param('checkret')
					check_ret=(int(checkret) == sess['code'])
				elif  g_blog.comment_check_type ==3:
					import app.gbtools as gb
					checknum=self.param('checknum')
					checkret=self.param('checkret')
					check_ret=eval(checknum)==int(gb.stringQ2B( checkret))

				if not check_ret:
					if useajax:
						self.write(simplejson.dumps((False,-102,_('Your check code is invalid .'))))
					else:
						self.error(-102,_('Your check code is invalid .'))
					return
			except:
				if useajax:
					self.write(simplejson.dumps((False,-102,_('Your check code is invalid .'))))
				else:
					self.error(-102,_('Your check code is invalid .'))
				return

		sess.invalidate()
		content=content.replace('\n','<br>')
		content=myfilter.do_filter(content)
		name=cgi.escape(name)[:20]
		url=cgi.escape(url)[:100]

		if not (name and email and content):
			if useajax:
				self.write(simplejson.dumps((False,-101,_('Please input name, email and comment .'))))
			else:
				self.error(-101,_('Please input name, email and comment .'))
		else:
			comment=Comment(author=name,
					content=content,
					email=email,
					reply_notify_mail=reply_notify_mail,
					entry=Entry.get(key))
			if url:
				try:
					comment.weburl=url
				except:
					comment.weburl=None
			info_str='#@#'.join([urlencode(name),urlencode(email),urlencode(url)])
			cookiestr=g_blog.tigger_adminurl('cookurl',info_str,\
			(datetime.now()+timedelta(days=100)).strftime("%a, %d-%b-%Y %H:%M:%S GMT"),'')
			comment.ip=self.request.remote_addr

			if parent_id:
				comment.parent=Comment.get_by_id(parent_id)

			try:
				comment.save()
				memcache.delete("/"+comment.entry.link)

				self.response.headers.add_header( 'Set-Cookie', cookiestr)
				if useajax:
					comment_c=self.get_render('comment',{'comment':comment})
					self.write(simplejson.dumps((True,comment_c.decode('utf8'))))
				else:
					self.redirect(self.referer+"#comment-"+str(comment.key().id()))

				comment.entry.removecache()
				memcache.delete("/feed/comments")
			except:
				if useajax:
					self.write(simplejson.dumps((False,-102,_('Comment not allowed.'))))
				else:
					self.error(-102,_('Comment not allowed .'))


class ChangeTheme(BaseRequestHandler):
    @requires_admin
    def get(self,slug=None):
       theme=self.param('t')
       g_blog.theme_name=theme
       g_blog.get_theme()
       self.redirect('/')


class do_action(BaseRequestHandler):
    def get(self,slug=None):

        try:
            func=getattr(self,'action_'+slug)
            if func and callable(func):
                func()
            else:
                self.error(404)
        except BaseException,e:
            self.error(404)

    def post(self,slug=None):
        try:
            func=getattr(self,'action_'+slug)
            if func and callable(func):
                func()
            else:
                self.error(404)
        except:
             self.error(404)

    @ajaxonly
    def action_info_login(self):
        if self.login_user:
            self.write(simplejson.dumps({'islogin':True,
                                         'isadmin':self.is_admin,
                                         'name': self.login_user.nickname()}))
        else:
            self.write(simplejson.dumps({'islogin':False}))

    #@hostonly
    @cache()
    def action_proxy(self):
        result=urlfetch.fetch(self.param("url"), headers=self.request.headers)
        if result.status_code == 200:
            self.response.headers['Expires'] = 'Thu, 15 Apr 3010 20:00:00 GMT'
            self.response.headers['Cache-Control'] = 'max-age=3600,public'
            self.response.headers['Content-Type'] = result.headers['Content-Type']
            self.response.out.write(result.content)
        return

    def action_getcomments(self):
        key=self.param('key')
        entry=Entry.get(key)
        comments=Comment.all().filter("entry =",key)

        commentuser=self.request.cookies.get('comment_user', '')
        if commentuser:
            commentuser=commentuser.split('#@#')
        else:
            commentuser=['','','']


        vals={
            'entry':entry,
            'comments':comments,
            'user_name':commentuser[0],
            'user_email':commentuser[1],
            'user_url':commentuser[2],
            'checknum1':random.randint(1,10),
            'checknum2':random.randint(1,10),
            }
        html=self.get_render('comments',vals)

        self.write(simplejson.dumps(html.decode('utf8')))

    def action_test(self):
        self.write(settings.LANGUAGE_CODE)
        self.write(_("this is a test"))


class getMedia(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self,slug):
        media=Media.get(slug)
        if media:
            self.send_blob(media.filekey.key())
            a=self.request.get('a')
            if a and a.lower()=='download':
                media.download+=1
                media.put()



class CheckImg(BaseRequestHandler):
    def get(self):
        img = Image()
        imgdata = img.create()
        sess=Session(self,timeout=900)
        if not sess.is_new():
            sess.invalidate()
            sess=Session(self,timeout=900)
        sess['code']=img.text
        sess.save()
        self.response.headers['Content-Type'] = "image/png"
        self.response.out.write(imgdata)


class CheckCode(BaseRequestHandler):
    def get(self):
        sess=Session(self,timeout=900)
        num1=random.randint(1,10)
        num2=random.randint(1,10)
        code="<span style='font-size:13px;color:red'>%d + %d =</span>"%(num1,num2)
        sess['code']=num1+num2
        sess.save()
        #self.response.headers['Content-Type'] = "text/html"
        self.response.out.write(code)



class Other(BaseRequestHandler):
    def get(self,slug=None):
        if not g_blog.tigger_urlmap(slug,page=self):
            self.error(404)

    def post(self,slug=None):
        content=g_blog.tigger_urlmap(slug,page=self)
        if content:
            self.write(content)
        else:
            self.error(404)

class Contact(BaseRequestHandler):

		@cache(time=36000,mime='text/html')
		def get(self,tags=None):
				title='Contact'
				self.render('contact',{'title':title})

class Join_us(BaseRequestHandler):

		@cache(time=36000,mime='text/html')
		def get(self,tags=None):
				title='Contact'
				self.render('joinus',{'value':OtherDoc().Getdoc('joinus')})

class About_me(BaseRequestHandler):

		@cache(time=36000,mime='text/html')
		def get(self,tags=None):
				title='Contact'
				self.render('aboutme',{'value':OtherDoc().Getdoc('aboutme')})


class Privacy(BaseRequestHandler):

		@cache(time=36000,mime='text/html')
		def get(self,tags=None):
				title='Contact'
				self.render('privacy',{'value':OtherDoc().Getdoc('privacy')})


class Support(BaseRequestHandler):

		@cache(time=36000,mime='text/html')
		def get(self,tags=None):
				title='Contact'
				self.render('support',{'title':title})






def getZipHandler(**args):
	return ('/xheditor/(.*)',zipserve.make_zip_handler('''D:\\work\\cdm\\plugins\\xheditor\\xheditor.zip'''))

def main():
	webapp.template.register_template_library('filter')
	webapp.template.register_template_library('app.recurse')
	urls= [('/checkimg/', CheckImg),
		('/checkcode/', CheckCode),
		('/skin',ChangeTheme),
		('/feed', FeedHandler),
		('/updatecount',Update_cate_count),
		('/feed/comments',CommentsFeedHandler),
		('/sitemap', SitemapHandler),
		('/post_comment',Post_comment),
		('/blog/post_comment',Post_comment),
		('/blog/page/(?P<page>\d+)', MainPage),
		('/download/page/(?P<page>\d+)', MainPage),
		('/article/page/(?P<page>\d+)', MainPage),
		('/category/(.*)',entriesByCategory),
		('/download/category/(.*)',entriesByCategory),
		('/article/category/(.*)',entriesByCategory),
		('/blog/category/(.*)',entriesByCategory),
		('/archive/(\d{4})/(\d{2})',archive_by_month),
		('/archive/(\d{4})/(\d{2})/(.*)',archive_by_month),
		('/tag/(.*)',entriesByTag),
		('/contact',Contact),
		('/privacy',Privacy),
		('/join',Join_us),
		('/aboutme',About_me),
		('/support',Support),
		#('/\?p=(?P<postid>\d+)',SinglePost),
		('/', MainPage),
		('/blog/', MainPage),
		('/download/', MainPage),
		('/download', MainPage),
		('/blog', MainPage),
		('/article/', MainPage),
		('/article', MainPage),
		('/do/(\w+)', do_action),
		('/e/(.*)',Other),
		('/download/([\w./%]+)', SinglePost),
		('/page/([\w./%]+)', SinglePost),
		('/download/([\w./%]+)/(.*)', SinglePost),
		('/article/([\w./%]+)', SinglePost),
		('/blog/([\w./%]+)', SinglePost),
		('/([\\w\\-\\./%]+)', SinglePost),
		('.*',Error404),
		]
	"""
	TODO:the debug set true for test
	"""
	application = webapp.WSGIApplication(urls,debug=True)
	g_blog.application=application
	g_blog.plugins.register_handlerlist(application)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
	main()
