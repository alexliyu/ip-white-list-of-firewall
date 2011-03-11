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
from google.appengine.ext.webapp import template, \
    WSGIApplication
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp import blobstore_handlers
from datetime import datetime ,timedelta
import base64,random
from django.utils import simplejson
import filter  as myfilter
from django.template.loader import *
from app import htmllib
from app.gmemsess import Session
from google.appengine.ext.blobstore import blobstore
from base import *
from model import *
import logging
from google.appengine.api import images
from google.appengine.ext import zipserve
from blog import CheckCode, CheckImg, Other, doRequestHandle, doRequestPostHandle
from google.appengine.api import memcache

#TODO THE BASE OF MEDIA FILES
class BaseMediaPage(BaseRequestHandler):
		def initialize(self, request, response):
				BaseRequestHandler.initialize(self,request, response)
				skey=request.path_qs
				#logging.info(skey)
				html= memcache.get(skey)
				if not html:
						p_categories=self.Tags()
						allmimes=Mime.all()
						latestphoto=Albums().GetlatestPhoto(9)
						topviews=Albums().Gettopviews(5)
						topcomments=Albums().Gettopcomment(5)
						self.template_vals.update({
								'categories':p_categories,
								'topviews':topviews,
								'allmimes':allmimes,
								'topcomments':topcomments,
								'latestphoto':latestphoto,
								'recent_comments':Media().Recentcomm()
					})
				##logging.info(latestphoto)

#TODO THE FUN OF THE BASE FOR MEDIA CATEGORIES
		@vcache(key='album_Tags')
		def Tags(self):
	    #TODO the tags of albums and media
				mytags=[]
				for tags in Albums.all().filter('tag != ',None):
						mytag=htmllib.decoding(tags.tag.tag)
						if mytag not in mytags:
								mytags.append(mytag)

				return mytags

		#def Rcomments(self,mime=None):
		#		mycomments=[]
		#		for comments in Media().all().filter('comments != ',None):
		#				mycomment=comments.comments
		#				if mycomment not in mycomments:
		#						mycomments.append(mycomment)
		#
		#		return mycomments


#TODO for the private media files
		@vcache(key='m_media')
		def m_media(self):
				return Media.all().filter('public =',False)\
								.order('-date')
		@vcache(key='m_album')
		def m_album(self):
				return Albums.all().filter('public =',False)\
								.order('-date')





#TODO THE MAIN PAGE OF ALBUM PAGES
class AlbumPage(BaseMediaPage):
		@cache(time=360000,mime='text/html')
		def get(self,page=1):
				postid=self.param('p')
				if postid:
						try:
								postid=int(postid)
								return doRequestHandle(self,ASinglePost(),postid=postid)  #singlepost.get(postid=postid)
						except:
								return self.error(404)
				self.doget(page)

		def post(self):
				postid=self.param('p')
				if postid:
						#try:
								postid=int(postid)
								return doRequestPostHandle(self,ASinglePost(),postid=postid)  #singlepost.get(postid=postid)
						#except:
						#		return self.error(404)

#TODO GET THE MEDIA PAGE
#TODO GET THE ALBUMS FOR ONE PAGE
		def doget(self,page):
				page=int(page)
				#TODO the g_blog.albumcount return the count of albums
				albumcount=g_blog.albumcount
				max_page = albumcount / g_blog.album_per_page + ( albumcount % g_blog.album_per_page and 1 or 0 )

				if max_page==0:max_page=1
				if page < 1 or page > max_page:
						return  self.error(404)

				albums = Albums.all().filter('public =',True).\
						order('-createdate').\
						fetch(self.blog.album_per_page, offset = (page-1) * self.blog.album_per_page)


				show_prev =albums and  (not (page == 1))
				show_next =albums and  (not (page == max_page))
				photos=Media().all().filter('public =',True).order('-date').fetch(50)
				latestphotos=Albums().GetlatestPhoto(9)
				return self.render('albums',{'albums':albums,
								'photos':photos,
								'show_prev' : show_prev,
								'show_next' : show_next,
								'pageindex':page,
								'latestphotos':latestphotos,
								})




#TODO RETURN THE album FILES BY TAG
class AlbumByTag(BaseMediaPage):
		@cache(time=36000,mime='text/html')
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
				albums=Albums().GetAlbumBytag(slug)
				if not albums:
						self.error(404)
				else:

						albums,links=Pager(query=albums,items_per_page=20).fetch(page_index)
						self.render('atag',{'albums':albums,'tag':slug,'pager':links})

#TODO THE SINGLE PAGE OF THE MEDIA FILE
class SinglePost(BaseMediaPage):
		@cache(time=36000,mime='text/html')
		def get(self,slug=None,postid=None):
				if postid:
						medias = Media.all().filter("public =", True).filter('post_id =', postid).fetch(1)
				else:
						slug=urldecode(slug)
						medias = media.all().filter("published =", True).filter('link =', slug).fetch(1)
				if not medias or len(medias) == 0:
						return self.error(404)

				mp=self.paramint("mp",1)

				media=medias[0]
				media.viewcount += 1
				media.put()
				self.media=media


				comments=media.comments


				commentuser=['','','']

				comments_nav=self.get_comments_nav(mp,media.comments.all().count())

				self.render('msingle',
						{
						'media':media,
						'comments':comments,
						'user_name':commentuser[0],
						'user_email':commentuser[1],
						'user_url':commentuser[2],
						'checknum1':random.randint(1,10),
						'checknum2':random.randint(1,10),
						'comments_nav':comments_nav,
						})


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
#TODO show images by Gallery

class GalleryShow(BaseMediaPage):
		@cache(time=36000,mime='text/html')
		def get(self,slug):
				#logging.info(slug)
				key=slug.split(".")[0]
				#logging.info(key)
				if db.get(key):
						albums=Albums().get(key)
						photos=albums.Photos()
						album_name=albums.albumname
				else:
						self.error(404)
				self.render('gallery',
						{
						'photos':photos,'album_name':album_name
						})


#TODO THE SINGLE PAGE OF THE ALBUM
class ASinglePost(BaseMediaPage):
		@cache(time=36000,mime='text/html')
		def get(self,slug=None,postid=None):
				postid=slug.split('.')
				postid=postid[0]
				albums=''
				if postid:
						albums = Albums().Getalbum(int(postid))
				if not albums:
						#logging.info(postid)
						return self.error(404)
				self.album=albums
				photos=self.album.media_set
				self.render('album',
						{
						'album':self.album,
						'photos':photos,
						})




#TODO THE SINGLE PAGE OF THE ALBUM
class PhotoPage(BaseMediaPage):
		@cache(time=36000,mime='text/html')
		def get(self,slug=None,postid=None):
				if postid ==None:
						postid=self.param('u')
						#logging.info(postid)
				photo=''
				if postid:
						photo = Media().get(postid)
				else:
						slug=urldecode(slug)
						photo = Media().all().filter('public =',True).filter('link =', slug).fetch(1)
				if not photo:
						return self.error(404)
				mp=self.paramint("mp",1)

				photo.viewcount += 1
				photo.put()
				self.photo=photo
				comments=photo.get_comments_by_page(mp,self.blog.comments_per_page)
				commentuser=['','','']
				count=len(comments)
				comments_nav=self.get_comments_nav(mp,photo.media_photo.count())
				self.render('photo',
						{
						'photo':self.photo,
						'comments':comments,
						'count':count,
						'user_name':commentuser[0],
						'user_email':commentuser[1],
						'user_url':commentuser[2],
						'checknum1':random.randint(1,10),
						'checknum2':random.randint(1,10),
						'comments_nav':comments_nav,
						})

		def get_comments_nav(self,pindex,count):
				#logging.info('pindex is %s,count is %s',pindex,count)
				maxpage=count / g_blog.comments_per_page + ( count % g_blog.comments_per_page and 1 or 0 )
				#logging.info(maxpage)
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
				url=str(self.photo.Link_url)

				if url.find('?')>=0:
						return g_blog.tigger_adminurl('entrycommurlo',url,str(pindex))
				else:
						return g_blog.tigger_adminurl('entrycommurlt',url,str(pindex))

		def Getcomments(self,photos,index,psize):
				comments=[]
				for photo in photos:
						for commentss in photo.media_photo:
								comments.append(commentss)
				if len(comments)>0:
						offset = (index-1) * psize
						return comments[offset:psize]
				else:
						return None
#TODO the rss of the media files
class FeedHandler(BaseRequestHandler):
    @cache(time=36000,mime='text/xml')
    def get(self,tags=None):
        medias = Media.all().filter('public =',True).order('-date').fetch(20)
        if medias and medias[0]:
            last_updated = medias[0].date
            last_updated = last_updated.strftime("%Y-%m-%dT%H:%M:%SZ")
        for e in medias:
            e.formatted_date = e.date.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.response.headers['Content-Type'] = 'application/atom+xml'
        self.render2('views/matom.xml',{'medias':medias,'last_updated':last_updated})




class Post_comment(BaseRequestHandler):
    #@printinfo
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
	#logging.info('i am here')
        if not self.is_login:
            #logging.info('i am here')
            #if not (self.request.cookies.get('comment_user', '')):
            try:
                check_ret=True
                if g_blog.comment_check_type in (1,2)  :
                    checkret=self.param('checkret')
                    check_ret=(int(checkret) == sess['code'])
		    #logging.info('checkret is %s,and check_ret is %s',checkret,check_ret)
                elif  g_blog.comment_check_type ==3:
                    import app.gbtools as gb
                    checknum=self.param('checknum')
                    checkret=self.param('checkret')
                    check_ret=eval(checknum)==int(gb.stringQ2B( checkret))
		    #logging.info('the checknum is %s,and the checkret is %s',checknum,checkret)
		#logging.info('the check_ret is %s',check_ret)
                if not check_ret:
                    if useajax:
                        self.write(simplejson.dumps((False,-102,_('Your check code is invalid .'))))
                    else:
                        self.error(-102,_('Your check code is invalid .'))
                    return
            except Exception,data:
	        #logging.info(data)
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
		#logging.info(key)
		comment=Acomment(author=name,
				content=content,
				email=email,
				reply_notify_mail=reply_notify_mail,
				photo=Media.get(key))
		if url:
				try:
						comment.weburl=url
				except:
						comment.weburl=None

            #name=name.decode('utf8').encode('gb2312')


		info_str='#@#'.join([urlencode(name),urlencode(email),urlencode(url)])

             #info_str='#@#'.join([name,email,url.encode('utf8')])
		cookiestr=g_blog.tigger_adminurl('cookurl',info_str,\
		(datetime.now()+timedelta(days=100)).strftime("%a, %d-%b-%Y %H:%M:%S GMT"),'')
		comment.ip=self.request.remote_addr

		if parent_id:
				comment.parent=Acomment.get_by_id(parent_id)

		try:
		    comment.save()
		    memcache.delete("/"+str(comment.photo.key()))

		    self.response.headers.add_header( 'Set-Cookie', cookiestr)
		    if useajax:
			comment_c=self.get_render('comment',{'comment':comment})
			self.write(simplejson.dumps((True,comment_c.decode('utf8'))))
		    else:
			self.redirect(self.referer+"#comment-"+str(comment.key().id()))

		    memcache.delete("/feed/comments")
		except Exception,data:
				#logging.info(data)
				if useajax:
						self.write(simplejson.dumps((False,-102,_('Comment not allowed.'))))
				else:
						self.error(-102,_('Comment not allowed .'))





class getMedia(blobstore_handlers.BlobstoreDownloadHandler,BaseRequestHandler):
		@cache(time=720000)
		def get(self,slug):
				media=Media.get(self.request.get('id'))
				if media:
						if g_blog.blobstore:
								self.send_blob(media.filekey.key())
						else:
								self.Post_data(media)
						a=self.request.get('action')
						if a and a.lower()=='download':
								media.download+=1
								media.put()




class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler,BaseRequestHandler):
		@cache(mime='image/jpg',time=720000)
		def get(self,slug):
				try:
						resource = self.request.query_string.split('.')[0]
						model=Media.get(resource)
						if g_blog.blobstore:
								blob_info = blobstore.BlobInfo.get(model.filekey.key())
								self.send_blob(blob_info)
						else:
								self.Post_data(model)
				except Exception:
					self.error(404)

class SSmallphotoHandler(BaseRequestHandler):
		@cache(mime='image/jpg',time=720000)
		def get(self,slug):
#TODO THE P IS THE KEY OF RESOURCE,THE W IS THE OUTPUT TYPE OF RESOURCE
			resulturl=self.Checkurl()
			if resulturl:

				try:
					#if not self.Chk_cache(3600,'image/jpeg'):
						resource = resulturl[0]
						resourcetype=resulturl[1]
						if g_blog.blobstore:
								rkey=self.Getkey(resource)

						else:
								rkey=self.GetModel(resource)

						img=self.Getdata(rkey,size=resourcetype)

						trfs=img.execute_transforms(output_encoding=images.JPEG)
						self.response.headers['Content-Type'] = 'image/jpeg'
						self.response.out.write(trfs)

				except Exception,data:
						#logging.info('the address is %s,and the error is %s',self.request.query_string,data)
						self.error(404)
			else:
				self.error(404)

		def Checkurl(self):
				theurl=[]
				if self.param('p'):
						theurl.append(self.param('p').split('.')[0])
				else:
						return None
				if self.param('w'):
						theurl.append(self.param('w'))
				else:
						return None
				return theurl


		def SmallCover(self,img):
				img.resize(width=130, height=94)
				return img

		def GalleryCover(self,img):
				img.resize(width=790, height=290)
				return img

		def MidCover(self,img):
				img.resize(width=150,height=150)
				return img

		def BigCover(self,img):
				img.resize(width=200,height=200)
				return img

		def CusCover(self,img,size):
				img.resize(width=int(size),height=int(size))
				return img

		def Getkey(self,resource):
				return Media.get(resource).filekey.key()

		def GetModel(self,resource):
				return Media.get(resource)

		def Getdata(self,mkey,gettype=None,buffer=None,size='m'):
				if g_blog.blobstore:
						blob_info = blobstore.BlobInfo.get(mkey)
						if gettype == None:

								if buffer!=None:
										blob_reader = blobstore.BlobReader(blob_info.key(),buffer_size=buffer)
								else:
										blob_reader = blobstore.BlobReader(blob_info.key())
								value = blob_reader.read()
								img = images.Image(value)

						else:
								img = images.Image(blob_key=blob_info.key())
				else:
						img = images.Image(mkey.blobfile)

				if size =='m':
						img=self.MidCover(img)
				elif size == 'b':
						img=self.BigCover(img)
				elif size == 's':
						img=self.SmallCover(img)
				elif size == 'g':
						img=self.GalleryCover(img)
				else:
						img=self.CusCover(img,size)

				img.im_feeling_lucky()
				return img




def main():
		webapp.template.register_template_library('filter')
		webapp.template.register_template_library('app.recurse')
		urls=   [('/media/([^/]*)/{0,1}.*',getMedia),
		('/serve/([^/]+)?', ServeHandler),
		('/sserve/(.*)',SSmallphotoHandler),
		('/album', AlbumPage),
		('/media/feed', FeedHandler),
		('/photo/post_comment',Post_comment),
		('/album/page/(?P<page>\d+)', AlbumPage),
		('/photo/(.*)', PhotoPage),
		('/album/tag/(.*)',AlbumByTag),
		('/media/([\w./%]+)', SinglePost),
		('/album/(.*)', ASinglePost),
		('/gallery/(.*)', GalleryShow),
		]
#TODO the debug set true for test,so if you feel good,you can change it to False
		application = webapp.WSGIApplication(urls,debug=True)
		g_blog.application=application
		g_blog.plugins.register_handlerlist(application)
		wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
		main()
